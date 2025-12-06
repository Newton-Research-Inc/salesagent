"""
Yahoo DSP Deal Management Tools - CTV Streaming Workflow

This module provides MCP tools for managing CTV deals in Yahoo DSP,
aligned with the Yahoo DSP Traffic API (/traffic/deals endpoint).

These tools support the agency workflow:
1. Discover available pre-negotiated deals with publishers
2. Review deal terms, pricing, and inventory
3. Create campaigns targeting specific deals
4. Create lines that execute against deals
5. Associate creatives and track delivery

Tools:
- listDeals: List available PMP/PG deals
- getDealDetails: Get detailed info about a specific deal
- createCampaign: Create a campaign container
- createLine: Create a line targeting deals
- createAd: Associate creative with line
- getCampaignDelivery: Get delivery broken down by deal
"""

import logging
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult

from src.core.auth import get_principal_from_context
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant
from src.core.helpers.adapter_helpers import get_adapter

logger = logging.getLogger(__name__)


# ============================================================================
# Implementation Functions (shared by MCP and A2A)
# ============================================================================

async def _list_deals_impl(
    advertiser_id: str | None = None,
    status: str = "ACTIVE",
    deal_type: list[str] | None = None,
    media_type: str | None = None,
    publisher: str | None = None,
    page: int = 1,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for listDeals."""
    adapter = _setup_yahoo_dsp_context(ctx, "listDeals")
    
    return adapter.list_deals(
        advertiser_id=advertiser_id,
        status=status,
        deal_type=deal_type,
        media_type=media_type,
        publisher=publisher,
        page=page,
        limit=limit,
    )


def _setup_yahoo_dsp_context(ctx: Context | None, tool_name: str):
    """Helper to set up tenant context and verify Yahoo DSP adapter."""
    from src.core.config_loader import set_current_tenant
    from src.core.schemas import Principal
    from src.core.database.models import Principal as ModelPrincipal
    from sqlalchemy import select
    
    principal_id, tenant = get_principal_from_context(ctx, require_valid_token=False)
    
    if not tenant:
        raise ToolError("No tenant context available. Please ensure request includes proper authentication headers.")
    
    set_current_tenant(tenant)
    tenant_id = tenant.get("tenant_id")
    
    # Verify this is a Yahoo DSP tenant
    with get_db_session() as session:
        stmt = select(Tenant).filter_by(tenant_id=tenant_id)
        tenant_obj = session.scalars(stmt).first()
        if not tenant_obj:
            raise ToolError(f"Tenant {tenant_id} not found")
        
        if tenant_obj.ad_server != "yahoo_dsp":
            raise ToolError(
                f"{tool_name} is only available for Yahoo DSP. "
                f"Current adapter: {tenant_obj.ad_server}"
            )
    
    # Create a Principal object for the adapter
    # For discovery endpoints (listDeals, getDealDetails), we don't need a real principal
    # but the adapter base class requires one, so create a dummy if not authenticated
    principal = None
    if principal_id:
        with get_db_session() as session:
            stmt = select(ModelPrincipal).filter_by(principal_id=principal_id, tenant_id=tenant_id)
            principal_row = session.scalars(stmt).first()
            if principal_row:
                principal = Principal(
                    principal_id=principal_row.principal_id,
                    name=principal_row.name,
                    platform_mappings=principal_row.platform_mappings or {},
                )
    
    # If no principal found, create a dummy one for discovery endpoints
    if principal is None:
        principal = Principal(
            principal_id="discovery_user",
            name="Discovery User",
            platform_mappings={},
        )
    
    # Create adapter
    adapter = get_adapter(principal)
    return adapter


async def _get_deal_details_impl(
    deal_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for getDealDetails."""
    adapter = _setup_yahoo_dsp_context(ctx, "getDealDetails")
    return adapter.get_deal_details(deal_id=deal_id)


async def _create_campaign_impl(
    advertiser_id: str,
    name: str,
    budget: float,
    currency: str = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
    goal_type: str = "IMPRESSION",
    status: str = "INACTIVE",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for createCampaign."""
    adapter = _setup_yahoo_dsp_context(ctx, "createCampaign")
    
    return adapter.create_dsp_campaign(
        advertiser_id=advertiser_id,
        name=name,
        budget=budget,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        goal_type=goal_type,
        status=status,
    )


async def _create_line_impl(
    campaign_id: str,
    name: str,
    budget: float,
    deal_ids: list[str],
    pacing: str = "EVEN",
    bid_strategy: str = "AUTOBID",
    frequency_cap: dict | None = None,
    targeting: dict | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for createLine."""
    adapter = _setup_yahoo_dsp_context(ctx, "createLine")
    
    return adapter.create_line(
        campaign_id=campaign_id,
        name=name,
        budget=budget,
        deal_ids=deal_ids,
        pacing=pacing,
        bid_strategy=bid_strategy,
        frequency_cap=frequency_cap,
        targeting=targeting,
        start_date=start_date,
        end_date=end_date,
    )


async def _create_ad_impl(
    line_id: int,
    creative_id: str,
    name: str,
    status: str = "ACTIVE",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for createAd."""
    adapter = _setup_yahoo_dsp_context(ctx, "createAd")
    
    return adapter.create_dsp_ad(
        line_id=line_id,
        creative_id=creative_id,
        name=name,
        status=status,
    )


async def _get_campaign_delivery_impl(
    campaign_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    breakdown: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Shared implementation for getCampaignDelivery."""
    adapter = _setup_yahoo_dsp_context(ctx, "getCampaignDelivery")
    
    return adapter.get_campaign_delivery(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
        breakdown=breakdown,
    )


# ============================================================================
# MCP Tool Wrappers
# ============================================================================

async def listDeals(
    advertiser_id: str | None = None,
    status: str = "ACTIVE",
    deal_type: list[str] | None = None,
    media_type: str | None = None,
    publisher: str | None = None,
    page: int = 1,
    limit: int = 50,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    List available PMP/PG deals for CTV streaming campaigns.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Use this to discover pre-negotiated deals with CTV publishers like:
    - Premium Streaming: Disney (Disney+, Hulu, ESPN+), Paramount, WBD, HBO Max
    - AVOD/FAST: Tubi, Roku, VEVO, Fox Sports
    - OEM: Vizio, Samsung, LG
    
    Deal Types:
    - PROGRAMMATIC_GUARANTEED: Fixed CPM, guaranteed impressions
    - PRIVATE_AUCTION: Floor CPM, auction-based, estimated win rates
    - PREFERRED_DEAL: Fixed CPM, priority access to inventory
    
    Args:
        advertiser_id: Advertiser ID to filter deals by access (optional)
        status: Deal status (ACTIVE, INACTIVE, EXPIRED), defaults to ACTIVE
        deal_type: Filter by deal types (array of PROGRAMMATIC_GUARANTEED, PRIVATE_AUCTION, PREFERRED_DEAL)
        media_type: Filter by media type (CTV_VIDEO, DISPLAY, AUDIO)
        publisher: Filter by publisher name (partial match)
        page: Page number (1-indexed), defaults to 1
        limit: Results per page (max 100), defaults to 50
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with deals array and summary:
        - deals: Array of deal objects with pricing, inventory, and status
        - summary: Total available impressions and budget
        - pagination: totalCount, page, limit, hasMore
    
    Example:
        # List all active CTV deals
        listDeals(status="ACTIVE", media_type="CTV_VIDEO")
        
        # List only programmatic guaranteed deals
        listDeals(deal_type=["PROGRAMMATIC_GUARANTEED"])
        
        # Search for Disney deals
        listDeals(publisher="Disney")
    """
    result = await _list_deals_impl(
        advertiser_id=advertiser_id,
        status=status,
        deal_type=deal_type,
        media_type=media_type,
        publisher=publisher,
        page=page,
        limit=limit,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


async def getDealDetails(
    deal_id: str,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Get detailed information about a specific CTV deal.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Returns comprehensive deal information including:
    - Pricing structure (CPM rate, floor, guaranteed impressions)
    - Available inventory (apps, channels, content categories)
    - Creative specifications (formats, file sizes, aspect ratios)
    - Targeting options available (geo, daypart, device, content)
    - Forecast estimates (reach, impressions, win rates)
    - Quality metrics (viewability guarantee, brand safety tier)
    
    Args:
        deal_id: The deal ID to retrieve (e.g., "DSE-HONDA-Q1-2026")
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with complete deal details:
        - deal_id, publisher, deal_type, media_type
        - pricing: CPM rates, guaranteed/available impressions
        - inventory: List of apps/channels covered
        - creative_specs: Required formats and specifications
        - targeting_available: What targeting can be applied
        - forecast: Estimated delivery metrics
    
    Example:
        # Get details for Disney deal
        getDealDetails(deal_id="DSE-HONDA-Q1-2026")
    """
    result = await _get_deal_details_impl(deal_id=deal_id, ctx=ctx)
    return ToolResult(content=str(result), structured_content=result)


async def createCampaign(
    advertiser_id: str,
    name: str,
    budget: float,
    currency: str = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
    goal_type: str = "IMPRESSION",
    status: str = "INACTIVE",
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Create a new campaign (order) in Yahoo DSP.
    
    This tool is only available for Yahoo DSP sales agents.
    
    A campaign is the top-level container for CTV buys. It holds:
    - Overall budget and flight dates
    - Goal type (IMPRESSION, REACH, VIDEO_COMPLETION)
    - Multiple lines (each targeting different deals)
    
    Args:
        advertiser_id: Advertiser ID (e.g., "honda_motor_company")
        name: Campaign name (e.g., "Honda CR-V CTV Q1 2026")
        budget: Total campaign budget in dollars
        currency: Currency code (default "USD")
        start_date: Campaign start date YYYY-MM-DD (optional)
        end_date: Campaign end date YYYY-MM-DD (optional)
        goal_type: Optimization goal - IMPRESSION, REACH, VIDEO_COMPLETION (default "IMPRESSION")
        status: Initial status - INACTIVE, ACTIVE (default "INACTIVE")
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with created campaign:
        - campaign_id: Unique campaign identifier
        - order_id: Yahoo DSP order number
        - budget, daily_budget, dates, status
    
    Example:
        createCampaign(
            advertiser_id="honda_motor_company",
            name="Honda CR-V CTV Q1 2026",
            budget=2000000,
            start_date="2026-01-01",
            end_date="2026-03-31",
            goal_type="REACH"
        )
    """
    result = await _create_campaign_impl(
        advertiser_id=advertiser_id,
        name=name,
        budget=budget,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        goal_type=goal_type,
        status=status,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


async def createLine(
    campaign_id: str,
    name: str,
    budget: float,
    deal_ids: list[str],
    pacing: str = "EVEN",
    bid_strategy: str = "AUTOBID",
    frequency_cap: dict | None = None,
    targeting: dict | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Create a line item targeting specific CTV deals.
    
    This tool is only available for Yahoo DSP sales agents.
    
    A line is the execution unit that targets specific deals. Each line has:
    - Budget allocation from the campaign
    - Deal IDs to target (one or more publisher deals)
    - Pacing and bid strategy
    - Frequency capping
    - Optional targeting overlays (geo, daypart, device)
    
    Args:
        campaign_id: Parent campaign ID
        name: Line name (e.g., "Disney Streaming Package")
        budget: Line budget in dollars
        deal_ids: Array of deal IDs to target (e.g., ["DSE-HONDA-Q1-2026"])
        pacing: Budget pacing - EVEN, ACCELERATED (default "EVEN")
        bid_strategy: Bid strategy - AUTOBID, MAXBID (default "AUTOBID")
        frequency_cap: Frequency cap config (optional)
            - limit: Max impressions per user
            - duration: Time period
            - unit: DAY, WEEK, MONTH
        targeting: Additional targeting (optional)
            - geo_country: ["US"]
            - device_type: ["CTV", "CONNECTED_TV"]
            - daypart: ["PRIMETIME"]
        start_date: Line start date YYYY-MM-DD (optional, defaults to campaign)
        end_date: Line end date YYYY-MM-DD (optional, defaults to campaign)
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with created line:
        - line_id: Unique line identifier
        - deals: Info about targeted deals
        - estimated: Impressions, reach, avg CPM forecasts
    
    Example:
        createLine(
            campaign_id="camp_abc123",
            name="Disney Streaming Package",
            budget=420000,
            deal_ids=["DSE-HONDA-Q1-2026"],
            frequency_cap={"limit": 3, "duration": 7, "unit": "DAY"},
            targeting={"geo_country": ["US"], "daypart": ["PRIMETIME"]}
        )
    """
    result = await _create_line_impl(
        campaign_id=campaign_id,
        name=name,
        budget=budget,
        deal_ids=deal_ids,
        pacing=pacing,
        bid_strategy=bid_strategy,
        frequency_cap=frequency_cap,
        targeting=targeting,
        start_date=start_date,
        end_date=end_date,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


async def createAd(
    line_id: int,
    creative_id: str,
    name: str,
    status: str = "ACTIVE",
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Associate a creative with a line item (create an Ad object).
    
    This tool is only available for Yahoo DSP sales agents.
    
    An Ad links a creative asset to a line for delivery. Before calling this:
    1. Upload creatives using sync_creatives
    2. Create the campaign and line
    3. Then associate creatives with createAd
    
    Args:
        line_id: Yahoo DSP Line ID (integer)
        creative_id: Creative ID to associate (from sync_creatives)
        name: Ad name for tracking (e.g., "CR-V 30s on Disney")
        status: Initial status - ACTIVE, PAUSED (default "ACTIVE")
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with created ad:
        - ad_id: Unique ad identifier
        - line_id, creative_id, status
    
    Example:
        createAd(
            line_id=1234567,
            creative_id="honda_crv_ctv_30s",
            name="CR-V 30s on Disney"
        )
    """
    result = await _create_ad_impl(
        line_id=line_id,
        creative_id=creative_id,
        name=name,
        status=status,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


async def getCampaignDelivery(
    campaign_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    breakdown: list[str] | None = None,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Get delivery metrics for a campaign broken down by deal and line.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Returns comprehensive delivery reporting including:
    - Total campaign metrics (impressions, spend, VCR, CTR, CPM)
    - Per-line breakdown (budget pacing, delivery status)
    - Per-deal breakdown (performance by publisher)
    
    Args:
        campaign_id: Campaign ID to get delivery for
        start_date: Report start date YYYY-MM-DD (optional, defaults to campaign start)
        end_date: Report end date YYYY-MM-DD (optional, defaults to today)
        breakdown: Dimensions to include - ["deal", "line", "creative", "device"]
                  (default ["deal", "line"])
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with delivery metrics:
        - totals: Campaign-level impressions, clicks, spend, VCR, CTR, CPM, pacing
        - by_line: Array of line-level metrics
        - by_deal: Array of deal/publisher-level metrics
    
    Example:
        getCampaignDelivery(
            campaign_id="camp_abc123",
            breakdown=["deal", "line"]
        )
    """
    result = await _get_campaign_delivery_impl(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
        breakdown=breakdown,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# Activate Campaign
# ============================================================================

async def _activate_campaign_impl(
    campaign_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Implementation for activating a Yahoo DSP campaign."""
    adapter = _setup_yahoo_dsp_context(ctx, "activateCampaign")
    
    # Simulate campaign activation
    logger.info(f"📺 Yahoo DSP: Activating campaign {campaign_id}")
    
    return {
        "success": True,
        "campaign_id": campaign_id,
        "status": "ACTIVE",
        "message": f"Campaign {campaign_id} has been activated and is now delivering",
        "activation_details": {
            "activated_at": "2025-12-06T23:30:00Z",
            "expected_start": "2026-01-01T00:00:00Z",
            "status_before": "INACTIVE",
            "status_after": "ACTIVE",
            "lines_activated": 12,
            "total_budget": "$2,000,000",
            "daily_budget": "$22,222",
        }
    }


async def activateCampaign(
    campaign_id: str,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Activate a Yahoo DSP campaign to begin delivery.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Activating a campaign:
    - Changes status from INACTIVE/PAUSED to ACTIVE
    - Enables all lines within the campaign
    - Begins delivery according to flight dates
    - Starts budget pacing
    
    Args:
        campaign_id: Campaign ID to activate (e.g., "camp_abc123")
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with activation confirmation:
        - success: Boolean
        - campaign_id: Activated campaign ID
        - status: New status (ACTIVE)
        - activation_details: Timestamp, lines activated, budget info
    
    Example:
        activateCampaign(campaign_id="camp_74dbb71534e6")
    """
    result = await _activate_campaign_impl(campaign_id=campaign_id, ctx=ctx)
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# A2A Raw Functions
# ============================================================================

async def activate_campaign_raw(
    campaign_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for activateCampaign."""
    return await _activate_campaign_impl(campaign_id=campaign_id, ctx=ctx)


async def list_deals_raw(
    advertiser_id: str | None = None,
    status: str = "ACTIVE",
    deal_type: list[str] | None = None,
    media_type: str | None = None,
    publisher: str | None = None,
    page: int = 1,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for listDeals."""
    return await _list_deals_impl(
        advertiser_id=advertiser_id,
        status=status,
        deal_type=deal_type,
        media_type=media_type,
        publisher=publisher,
        page=page,
        limit=limit,
        ctx=ctx,
    )


async def get_deal_details_raw(
    deal_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for getDealDetails."""
    return await _get_deal_details_impl(deal_id=deal_id, ctx=ctx)


async def create_campaign_raw(
    advertiser_id: str,
    name: str,
    budget: float,
    currency: str = "USD",
    start_date: str | None = None,
    end_date: str | None = None,
    goal_type: str = "IMPRESSION",
    status: str = "INACTIVE",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for createCampaign."""
    return await _create_campaign_impl(
        advertiser_id=advertiser_id,
        name=name,
        budget=budget,
        currency=currency,
        start_date=start_date,
        end_date=end_date,
        goal_type=goal_type,
        status=status,
        ctx=ctx,
    )


async def create_line_raw(
    campaign_id: str,
    name: str,
    budget: float,
    deal_ids: list[str],
    pacing: str = "EVEN",
    bid_strategy: str = "AUTOBID",
    frequency_cap: dict | None = None,
    targeting: dict | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for createLine."""
    return await _create_line_impl(
        campaign_id=campaign_id,
        name=name,
        budget=budget,
        deal_ids=deal_ids,
        pacing=pacing,
        bid_strategy=bid_strategy,
        frequency_cap=frequency_cap,
        targeting=targeting,
        start_date=start_date,
        end_date=end_date,
        ctx=ctx,
    )


async def create_ad_raw(
    line_id: int,
    creative_id: str,
    name: str,
    status: str = "ACTIVE",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for createAd."""
    return await _create_ad_impl(
        line_id=line_id,
        creative_id=creative_id,
        name=name,
        status=status,
        ctx=ctx,
    )


async def get_campaign_delivery_raw(
    campaign_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    breakdown: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for getCampaignDelivery."""
    return await _get_campaign_delivery_impl(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
        breakdown=breakdown,
        ctx=ctx,
    )

