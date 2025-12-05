"""
Yahoo DSP Audience Tools for MCP.

These tools expose Yahoo DSP's native audience discovery and analytics capabilities,
allowing Newton to discover, evaluate, and select audience segments.

Tools:
- getAudienceSegments: Query available audience segments with filters
- Get_analytics_for_audiences_segment: Get analytics for specific segments
"""

import logging
from typing import Any

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from fastmcp.tools.tool import ToolResult

from src.adapters import get_adapter
from src.core.auth import get_principal_from_context
from src.core.config_loader import load_config
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant

logger = logging.getLogger(__name__)


# =============================================================================
# Implementation Functions
# =============================================================================


async def _get_audience_segments_impl(
    account_id: str | int | None,
    segment_type: str | None,
    status: str,
    keywords: str | None,
    query: str | None,
    country_codes: str | None,
    page: int,
    limit: int,
    include_iab_data_labels: bool,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Implementation for getAudienceSegments.
    
    Queries available audience segments from Yahoo DSP with filters.
    Only available for Yahoo DSP adapter.
    
    Args:
        account_id: Advertiser ID (optional)
        segment_type: Filter by type (INTEREST, FACT, LOOKALIKE, CONVERSIONRULE, SRT, GEORETARGET)
        status: Segment status (ACTIVE, INACTIVE)
        keywords: Comma-separated search strings
        query: Search by name
        country_codes: Country ISO3 codes (comma-separated)
        page: Page number (1-indexed)
        limit: Results per page (max 100)
        include_iab_data_labels: Include IAB data labels in response
        ctx: MCP context (optional for direct calls)
        
    Returns:
        Dict with segments list, pagination info, and total count
        
    Raises:
        ToolError: If adapter is not Yahoo DSP or other errors occur
    """
    from src.core.config_loader import set_current_tenant
    from src.core.schemas import Principal
    
    # IMPORTANT: Must call get_principal_from_context FIRST to set up tenant context
    # For discovery endpoints, authentication is optional (require_valid_token=False)
    principal_id, tenant = get_principal_from_context(ctx, require_valid_token=False)
    
    if tenant:
        set_current_tenant(tenant)
        tenant_id = tenant.get("tenant_id")
    else:
        raise ToolError("No tenant context available. Please ensure request includes proper authentication headers.")
    
    # Load tenant config from database
    with get_db_session() as session:
        from sqlalchemy import select
        stmt = select(Tenant).filter_by(tenant_id=tenant_id)
        tenant_obj = session.scalars(stmt).first()
        if not tenant_obj:
            raise ToolError(f"Tenant {tenant_id} not found")
        
        adapter_type = tenant_obj.ad_server
    
    # Verify this is a Yahoo DSP tenant
    if adapter_type != "yahoo_dsp":
        raise ToolError(
            f"getAudienceSegments is only available for Yahoo DSP. "
            f"Current adapter: {adapter_type}"
        )
    
    # Create a Principal object for the adapter
    principal = None
    if principal_id:
        # Get principal data from database
        with get_db_session() as session:
            from src.core.database.models import Principal as ModelPrincipal
            from sqlalchemy import select
            stmt = select(ModelPrincipal).filter_by(principal_id=principal_id, tenant_id=tenant_id)
            principal_row = session.scalars(stmt).first()
            if principal_row:
                principal = Principal(
                    principal_id=principal_row.principal_id,
                    name=principal_row.name,
                    platform_mappings=principal_row.platform_mappings or {},
                )
    
    # Load config and create adapter
    config = load_config()
    adapter = get_adapter(config, principal)
    
    # Verify adapter name
    if adapter.adapter_name != "yahoo_dsp":
        raise ToolError(
            f"getAudienceSegments is only available for Yahoo DSP adapter. "
            f"Got: {adapter.adapter_name}"
        )
    
    # Convert account_id to int if it's a numeric string, otherwise ignore non-numeric values
    resolved_account_id = None
    if account_id is not None:
        if isinstance(account_id, int):
            resolved_account_id = account_id
        elif isinstance(account_id, str):
            # Try to parse as int, otherwise ignore (it might be a name like "Honda")
            try:
                resolved_account_id = int(account_id)
            except ValueError:
                # Non-numeric string like "Honda" - ignore it, we'll return all segments
                logger.info(f"accountId '{account_id}' is not numeric, ignoring filter")
                resolved_account_id = None
    
    # Call adapter method
    try:
        result = adapter.get_audience_segments(
            account_id=resolved_account_id,
            segment_type=segment_type,
            status=status,
            keywords=keywords,
            query=query,
            country_codes=country_codes,
            page=page,
            limit=limit,
            include_iab_data_labels=include_iab_data_labels,
        )
        return result
    except Exception as e:
        logger.error(f"Error in getAudienceSegments: {e}", exc_info=True)
        raise ToolError(f"Failed to get audience segments: {str(e)}")


async def _get_segment_analytics_impl(
    segment_ids: list[int],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Implementation for Get_analytics_for_audiences_segment.
    
    Retrieves analytics for specific audience segments including reach,
    CPM, CTR, conversion rates, and overlap analysis.
    Only available for Yahoo DSP adapter.
    
    Args:
        segment_ids: List of segment IDs to get analytics for
        ctx: MCP context (optional for direct calls)
        
    Returns:
        Dict with segmentAnalytics array containing metrics for each segment
        
    Raises:
        ToolError: If adapter is not Yahoo DSP or other errors occur
    """
    from src.core.config_loader import set_current_tenant
    from src.core.schemas import Principal
    
    # IMPORTANT: Must call get_principal_from_context FIRST to set up tenant context
    principal_id, tenant = get_principal_from_context(ctx, require_valid_token=False)
    
    if tenant:
        set_current_tenant(tenant)
        tenant_id = tenant.get("tenant_id")
    else:
        raise ToolError("No tenant context available. Please ensure request includes proper authentication headers.")
    
    # Load tenant config from database
    with get_db_session() as session:
        from sqlalchemy import select
        stmt = select(Tenant).filter_by(tenant_id=tenant_id)
        tenant_obj = session.scalars(stmt).first()
        if not tenant_obj:
            raise ToolError(f"Tenant {tenant_id} not found")
        
        adapter_type = tenant_obj.ad_server
    
    # Verify this is a Yahoo DSP tenant
    if adapter_type != "yahoo_dsp":
        raise ToolError(
            f"Get_analytics_for_audiences_segment is only available for Yahoo DSP. "
            f"Current adapter: {adapter_type}"
        )
    
    # Create a Principal object for the adapter
    principal = None
    if principal_id:
        with get_db_session() as session:
            from src.core.database.models import Principal as ModelPrincipal
            from sqlalchemy import select
            stmt = select(ModelPrincipal).filter_by(principal_id=principal_id, tenant_id=tenant_id)
            principal_row = session.scalars(stmt).first()
            if principal_row:
                principal = Principal(
                    principal_id=principal_row.principal_id,
                    name=principal_row.name,
                    platform_mappings=principal_row.platform_mappings or {},
                )
    
    # Load config and create adapter
    config = load_config()
    adapter = get_adapter(config, principal)
    
    # Verify adapter name
    if adapter.adapter_name != "yahoo_dsp":
        raise ToolError(
            f"Get_analytics_for_audiences_segment is only available for Yahoo DSP adapter. "
            f"Got: {adapter.adapter_name}"
        )
    
    # Validate input
    if not segment_ids:
        raise ToolError("At least one segment ID is required")
    
    # Call adapter method
    try:
        result = adapter.get_segment_analytics(segment_ids=segment_ids)
        return result
    except Exception as e:
        logger.error(f"Error in Get_analytics_for_audiences_segment: {e}", exc_info=True)
        raise ToolError(f"Failed to get segment analytics: {str(e)}")


# =============================================================================
# MCP Tool Wrappers (registered in main.py)
# =============================================================================


async def getAudienceSegments(
    accountId: str | int | None = None,
    segmentType: str | None = None,
    status: str = "ACTIVE",
    keywords: str | None = None,
    query: str | None = None,
    countryCodes: str | None = None,
    page: int = 1,
    limit: int = 50,
    includeIabDataLabels: bool = False,
    ctx: Context | None = None,
    # Newton-specific parameters (ignored but accepted for compatibility)
    super_access: bool = False,
) -> ToolResult:
    """
    Returns a list of audience segments based on the provided filters.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Segment types:
    - INTEREST: Yahoo behavioral segments (e.g., "Auto Intenders - SUV/Crossover")
    - FACT: Third-party data segments from Oracle, Experian, Polk/IHS Markit
    - LOOKALIKE: Modeled audiences based on seed audience (e.g., "Honda Website Converters - Lookalike")
    - CONVERSIONRULE: Pixel-based retargeting segments (e.g., "Honda.com - CR-V Page Visitors")
    - SRT: Search keyword audiences based on Yahoo search behavior
    - GEORETARGET: Point-of-interest audiences (e.g., "Honda Dealership Visitors")
    
    Args:
        accountId: Advertiser ID to filter segments by (optional)
        segmentType: Filter by segment type (INTEREST, FACT, LOOKALIKE, CONVERSIONRULE, SRT, GEORETARGET)
        status: Segment status filter (ACTIVE or INACTIVE), defaults to ACTIVE
        keywords: Comma-separated search terms to match against name, description, and keywords
        query: Search by name only
        countryCodes: Comma-separated country ISO3 codes (e.g., "USA,CAN")
        page: Page number (1-indexed), defaults to 1
        limit: Results per page (max 100), defaults to 50
        includeIabDataLabels: Include IAB data labels in response, defaults to False
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with segments array and pagination info:
        - segments: Array of segment objects with id, name, segmentType, reach, description, etc.
        - totalCount: Total number of matching segments
        - page: Current page number
        - limit: Results per page
        - hasMore: Whether more results are available
    
    Example:
        # Find automotive audience segments
        getAudienceSegments(
            segmentType="INTEREST",
            keywords="auto, SUV, crossover, honda",
            status="ACTIVE"
        )
    """
    result = await _get_audience_segments_impl(
        account_id=accountId,
        segment_type=segmentType,
        status=status,
        keywords=keywords,
        query=query,
        country_codes=countryCodes,
        page=page,
        limit=limit,
        include_iab_data_labels=includeIabDataLabels,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


async def Get_analytics_for_audiences_segment(
    segmentIds: str,
    ctx: Context | None = None,
    # Newton-specific parameters (ignored but accepted for compatibility)
    super_access: bool = False,
) -> ToolResult:
    """
    Retrieve analytics for specific audience segments by segmentId.
    
    This tool is only available for Yahoo DSP sales agents.
    
    Returns detailed analytics for each segment including:
    - reach: Total addressable audience size
    - avgCPM: Average CPM for this segment
    - historicalCTR: Historical click-through rate
    - viewabilityRate: Viewability rate for impressions
    - conversionRate: Conversion rate from clicks
    - dealerVisitRate: Dealer visit rate (for auto campaigns)
    - overlapAnalysis: Overlap percentages with other requested segments
    - performanceIndex: Overall performance score (0-100)
    - recommendation: Strategic recommendation (SCALE, CONQUEST, CORE, CONVERSION, RETARGETING)
    
    Args:
        segmentIds: Comma-separated segment IDs (e.g., "98765,98766,98767")
        ctx: MCP context (injected automatically)
    
    Returns:
        ToolResult with segmentAnalytics array containing metrics for each segment
    
    Example:
        # Get analytics for automotive segments discovered via getAudienceSegments
        Get_analytics_for_audiences_segment(segmentIds="98765,98766,98767,98768")
    """
    # Parse comma-separated segment IDs
    try:
        segment_id_list = [int(s.strip()) for s in segmentIds.split(",") if s.strip()]
    except ValueError as e:
        raise ToolError(f"Invalid segment ID format. Expected comma-separated integers: {e}")
    
    if not segment_id_list:
        raise ToolError("At least one segment ID is required")
    
    result = await _get_segment_analytics_impl(
        segment_ids=segment_id_list,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


# =============================================================================
# A2A Raw Functions (for agent-to-agent calls without MCP)
# =============================================================================


async def get_audience_segments_raw(
    account_id: int | None = None,
    segment_type: str | None = None,
    status: str = "ACTIVE",
    keywords: str | None = None,
    query: str | None = None,
    country_codes: str | None = None,
    page: int = 1,
    limit: int = 50,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    A2A raw function for getAudienceSegments.
    
    Same as getAudienceSegments but returns raw dict without ToolResult wrapper.
    """
    return await _get_audience_segments_impl(
        account_id=account_id,
        segment_type=segment_type,
        status=status,
        keywords=keywords,
        query=query,
        country_codes=country_codes,
        page=page,
        limit=limit,
        include_iab_data_labels=False,
        ctx=ctx,
    )


async def get_segment_analytics_raw(
    segment_ids: list[int],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    A2A raw function for Get_analytics_for_audiences_segment.
    
    Same as Get_analytics_for_audiences_segment but returns raw dict without ToolResult wrapper.
    """
    return await _get_segment_analytics_impl(
        segment_ids=segment_ids,
        ctx=ctx,
    )

