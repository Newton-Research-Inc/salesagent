"""
Yahoo DSP Live Adapter - Real API Integration

This adapter provides REAL Yahoo DSP API integration, following the modular
architecture pattern established by the GAM adapter.

NOTE: The existing yahoo_dsp_simulated.py (YahooDSPSimulated class) remains unchanged 
as the SIMULATION adapter for demos and testing. This adapter uses real API calls.

Yahoo DSP Object Hierarchy:
- Advertiser → Campaign (Order) → Line (Package) → Ad (Creative Assignment)

Configuration Required:
- client_id: Yahoo DSP OAuth client ID
- client_secret: Yahoo DSP OAuth client secret
- seat_id: Yahoo DSP seat (account) ID
- advertiser_id: Yahoo DSP advertiser ID

Authentication:
- Uses JWT client assertion flow (HS256 signed with client_secret)
- Token endpoint: https://id.b2b.yahooinc.com/identity/oauth2/access_token
- API uses X-Auth-Method and X-Auth-Token headers (NOT Bearer token)

Reference: https://help.yahooinc.com/dsp-api/docs/dsp-api-help-home
"""

import logging
from datetime import datetime
from typing import Any

from adcp.types import PackageStatus
from adcp.types.aliases import Package as ResponsePackage

from src.adapters.base import AdServerAdapter
from src.adapters.yahoo_dsp.auth import YahooDSPAuthManager
from src.adapters.yahoo_dsp.client import YahooDSPClient
from src.adapters.yahoo_dsp.config import YahooDSPConfig
from src.adapters.yahoo_dsp.managers import (
    YahooDSPAdManager,
    YahooDSPCampaignManager,
    YahooDSPCreativeManager,
    YahooDSPLineManager,
    YahooDSPReportingManager,
)
from src.adapters.yahoo_dsp.utils.constants import (
    YahooToAdCPStatusMapping,
)
from src.core.audit_logger import AuditLogger
from src.core.schemas import (
    AdapterGetMediaBuyDeliveryResponse,
    AssetStatus,
    CheckMediaBuyStatusResponse,
    CreateMediaBuyError,
    CreateMediaBuyRequest,
    CreateMediaBuySuccess,
    DeliveryTotals,
    Error,
    MediaPackage,
    PackagePerformance,
    ReportingPeriod,
    UpdateMediaBuyError,
    UpdateMediaBuyResponse,
    UpdateMediaBuySuccess,
)

logger = logging.getLogger(__name__)


class YahooDSPLive(AdServerAdapter):
    """Yahoo DSP adapter using REAL API endpoints.

    This adapter connects to the actual Yahoo DSP API for programmatic buying.
    It uses the modular architecture pattern with specialized managers for
    different operation types.

    Key Differences from YahooDSPSimulated (simulation):
    - Uses real HTTP API calls instead of in-memory storage
    - Requires valid OAuth credentials (JWT-based authentication)
    - Subject to Yahoo DSP rate limits and policies
    - Campaigns persist in Yahoo DSP platform

    Use this adapter for production deployments with real Yahoo DSP accounts.
    Use yahoo_dsp_simulated (YahooDSPSimulated) for demos, testing, and development.
    """

    adapter_name = "yahoo_dsp_live"

    # Supported pricing models (Yahoo DSP supports programmatic buying)
    SUPPORTED_PRICING_MODELS = {"cpm", "vcpm", "cpc", "cpcv", "flat_rate"}

    # Maximum budget in cents for test mode ($5.00)
    TEST_MODE_MAX_BUDGET_CENTS = 500

    def __init__(
        self,
        config: dict[str, Any],
        principal,
        *,
        seat_id: str | None = None,
        advertiser_id: str | None = None,
        dry_run: bool = False,
        test_mode: bool = False,
        audit_logger: AuditLogger | None = None,
        tenant_id: str | None = None,
    ):
        """Initialize Yahoo DSP Live adapter.

        Args:
            config: Configuration dictionary containing:
                - client_id: OAuth client ID
                - client_secret: OAuth client secret
                - seat_id: DSP seat ID (can also pass as parameter)
                - advertiser_id: Advertiser ID (can also pass as parameter)
                - test_mode: If True, create campaigns as INACTIVE with max $5 budget
            principal: Principal object for authentication
            seat_id: Yahoo DSP seat ID (overrides config)
            advertiser_id: Yahoo DSP advertiser ID (overrides config)
            dry_run: If True, log API calls but don't execute
            test_mode: If True, create campaigns as INACTIVE with capped budget (safe testing)
            audit_logger: Audit logging instance
            tenant_id: Tenant identifier
        """
        super().__init__(config, principal, dry_run, None, tenant_id)
        
        # Test mode creates INACTIVE campaigns with capped budget
        self.test_mode = test_mode or config.get("test_mode", False)

        # Build validated configuration
        self.yahoo_config = YahooDSPConfig.from_dict({
            **config,
            "seat_id": seat_id or config.get("seat_id"),
            "advertiser_id": advertiser_id or config.get("advertiser_id"),
        })

        # Validate configuration
        is_valid, error = self.yahoo_config.validate()
        if not is_valid:
            raise ValueError(f"Invalid Yahoo DSP configuration: {error}")

        # Initialize authentication (JWT-based)
        self.auth_manager = YahooDSPAuthManager(
            client_id=self.yahoo_config.client_id,
            client_secret=self.yahoo_config.client_secret,
        )

        # Initialize API client
        self.client = YahooDSPClient(
            auth_manager=self.auth_manager,
            seat_id=self.yahoo_config.seat_id,
            api_base_url=self.yahoo_config.api_base_url,
            dry_run=dry_run,
        )

        # Initialize managers
        self.campaigns = YahooDSPCampaignManager(
            client=self.client,
            advertiser_id=self.yahoo_config.advertiser_id,
        )
        self.lines = YahooDSPLineManager(client=self.client)
        self.ads = YahooDSPAdManager(client=self.client)
        self.creatives = YahooDSPCreativeManager(
            client=self.client,
            advertiser_id=self.yahoo_config.advertiser_id,
        )
        self.reporting = YahooDSPReportingManager(
            client=self.client,
            advertiser_id=self.yahoo_config.advertiser_id,
        )

        logger.info(
            f"Initialized Yahoo DSP Live adapter (seat: {self.yahoo_config.seat_id}, "
            f"advertiser: {self.yahoo_config.advertiser_id}, dry_run: {dry_run}, test_mode: {self.test_mode})"
        )
        
        if self.test_mode:
            logger.warning(
                "⚠️ TEST MODE ENABLED: Campaigns will be created as PAUSED with max $5 budget"
            )

    def get_supported_pricing_models(self) -> set[str]:
        """Return set of pricing models this adapter supports."""
        return self.SUPPORTED_PRICING_MODELS

    def create_media_buy(
        self,
        request: CreateMediaBuyRequest,
        packages: list[MediaPackage],
        start_time: datetime,
        end_time: datetime,
        package_pricing_info: dict[str, dict] | None = None,
    ) -> CreateMediaBuySuccess | CreateMediaBuyError:
        """Create a new media buy (Campaign + Lines) in Yahoo DSP.

        This creates:
        1. A Campaign (equivalent to GAM Order)
        2. One Line per package (equivalent to GAM Line Items)

        Args:
            request: Full create media buy request
            packages: Simplified package models for adapter
            start_time: Campaign start time
            end_time: Campaign end time
            package_pricing_info: Validated pricing information per package

        Returns:
            CreateMediaBuySuccess on success, CreateMediaBuyError on failure
        """
        try:
            # Test mode safeguards - use PAUSED for inactive campaigns (Yahoo's term)
            campaign_status = "PAUSED" if self.test_mode else "ACTIVE"
            line_status = "PAUSED" if self.test_mode else "ACTIVE"
            
            self.audit_logger.log_operation(
                operation="create_media_buy",
                principal_name=self.principal.name,
                principal_id=self.principal.principal_id,
                adapter_id=self.yahoo_config.advertiser_id or "unknown",
                success=True,
                details={
                    "buyer_ref": request.buyer_ref,
                    "package_count": len(packages),
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "test_mode": self.test_mode,
                    "status": "started",
                },
            )

            # Calculate total budget (cap in test mode)
            total_budget = sum(p.budget for p in packages)
            if self.test_mode and total_budget > self.TEST_MODE_MAX_BUDGET_CENTS:
                logger.warning(
                    f"TEST MODE: Capping total budget from {total_budget} to {self.TEST_MODE_MAX_BUDGET_CENTS} cents"
                )
                total_budget = self.TEST_MODE_MAX_BUDGET_CENTS

            # Create Campaign
            # Use campaign_name if provided, otherwise derive from buyer_ref or brand_manifest
            display_name = request.campaign_name or request.buyer_ref or "Campaign"
            campaign_name = f"{display_name}"
            if self.test_mode:
                campaign_name = f"[TEST] {campaign_name}"
                
            campaign = self.campaigns.create_campaign(
                name=campaign_name,
                budget=total_budget,
                start_date=start_time,
                end_date=end_time,
                status=campaign_status,
                metadata={
                    "external_id": request.buyer_ref,
                    "labels": ["adcp", "automated"] + (["test"] if self.test_mode else []),
                },
            )

            campaign_id = str(campaign.get("id"))
            logger.info(f"Created Yahoo DSP campaign: {campaign_id} (status: {campaign_status})")

            # Create Lines for each package
            created_packages = []
            for package in packages:
                try:
                    # Determine media type
                    media_type = self._determine_media_type(package)

                    # Get bid strategy from pricing info
                    bid_strategy = "AUTOBID"
                    max_bid = None
                    if package_pricing_info and package.package_id in package_pricing_info:
                        pricing = package_pricing_info[package.package_id]
                        if pricing.get("is_fixed"):
                            bid_strategy = "MAXBID"
                            max_bid = pricing.get("bid_price")

                    # Cap line budget in test mode
                    line_budget = package.budget
                    if self.test_mode and line_budget > self.TEST_MODE_MAX_BUDGET_CENTS:
                        line_budget = self.TEST_MODE_MAX_BUDGET_CENTS
                        
                    # Create Line
                    line_name = package.name or f"Package {package.package_id}"
                    if self.test_mode:
                        line_name = f"[TEST] {line_name}"
                        
                    line = self.lines.create_line(
                        campaign_id=campaign_id,
                        name=line_name,
                        budget=line_budget,
                        media_type=media_type,
                        status=line_status,
                        start_date=start_time,
                        end_date=end_time,
                        bid_strategy=bid_strategy,
                        max_bid=max_bid,
                        targeting=self._build_targeting(package),
                    )

                    line_id = str(line.get("id"))
                    logger.info(f"Created Yahoo DSP line: {line_id} (status: {line_status})")

                    created_packages.append(
                        ResponsePackage(
                            package_id=package.package_id,
                            platform_line_item_id=line_id,
                            status=PackageStatus.PENDING_APPROVAL,
                        )
                    )

                except Exception as e:
                    logger.error(f"Failed to create line for package {package.package_id}: {e}")
                    created_packages.append(
                        ResponsePackage(
                            package_id=package.package_id,
                            platform_line_item_id="",
                            status=PackageStatus.REJECTED,
                        )
                    )

            self.audit_logger.log_operation(
                operation="create_media_buy",
                principal_name=self.principal.name,
                principal_id=self.principal.principal_id,
                adapter_id=self.yahoo_config.advertiser_id or "unknown",
                success=True,
                details={
                    "campaign_id": campaign_id,
                    "line_count": len(created_packages),
                    "status": "completed",
                },
            )

            return CreateMediaBuySuccess(
                media_buy_id=campaign_id,
                buyer_ref=request.buyer_ref or "unknown",
                packages=created_packages,
            )

        except Exception as e:
            logger.exception(f"Failed to create media buy: {e}")
            self.audit_logger.log_operation(
                operation="create_media_buy",
                principal_name=self.principal.name,
                principal_id=self.principal.principal_id,
                adapter_id=self.yahoo_config.advertiser_id or "unknown",
                success=False,
                error=str(e),
            )

            return CreateMediaBuyError(
                errors=[Error(
                    code="CREATION_FAILED",
                    message=f"Failed to create media buy: {str(e)}",
                    details=None,
                )]
            )

    def add_creative_assets(
        self,
        media_buy_id: str,
        assets: list[dict[str, Any]],
        today: datetime,
    ) -> list[AssetStatus]:
        """Add creative assets to an existing media buy.

        This:
        1. Creates Creatives in Yahoo DSP
        2. Creates Ads to link Creatives to Lines

        Args:
            media_buy_id: Campaign ID
            assets: List of creative asset specifications
            today: Current date for validation

        Returns:
            List of asset status objects
        """
        logger.info(f"Adding {len(assets)} creative assets to campaign {media_buy_id}")

        results = []

        # Get lines for this campaign
        lines = self.lines.list_lines(campaign_id=media_buy_id)

        if not lines:
            logger.error(f"No lines found for campaign {media_buy_id}")
            for asset in assets:
                results.append(
                    AssetStatus(
                        asset_id=asset.get("creative_id", "unknown"),
                        status="error",
                        message="No lines found for campaign",
                    )
                )
            return results

        # Process each asset
        for asset in assets:
            try:
                # Create creative
                creative = self.creatives.create_creative_from_adcp(asset)
                creative_id = str(creative.get("id"))

                # Associate with all lines (or specific line if specified)
                target_line_id = asset.get("package_id") or str(lines[0].get("id"))

                ad = self.ads.create_ad(
                    line_id=target_line_id,
                    creative_id=creative_id,
                    name=asset.get("name", f"Creative {creative_id}"),
                )

                results.append(
                    AssetStatus(
                        asset_id=asset.get("creative_id", creative_id),
                        status="pending",
                        platform_creative_id=creative_id,
                        message=f"Creative uploaded, Ad ID: {ad.get('id')}",
                    )
                )

            except Exception as e:
                logger.error(f"Failed to add creative asset: {e}")
                results.append(
                    AssetStatus(
                        asset_id=asset.get("creative_id", "unknown"),
                        status="error",
                        message=str(e),
                    )
                )

        return results

    def associate_creatives(
        self,
        line_item_ids: list[str],
        platform_creative_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Associate already-uploaded creatives with line items.

        Args:
            line_item_ids: Platform-specific line IDs
            platform_creative_ids: Platform-specific creative IDs

        Returns:
            List of association results
        """
        logger.info(f"Associating {len(platform_creative_ids)} creatives with {len(line_item_ids)} lines")

        results = []
        for line_id in line_item_ids:
            line_results = self.ads.associate_creatives_with_line(
                line_id=line_id,
                creative_ids=platform_creative_ids,
            )
            results.extend(line_results)

        return results

    def check_media_buy_status(
        self,
        media_buy_id: str,
        today: datetime,
    ) -> CheckMediaBuyStatusResponse:
        """Check the status of a media buy.

        Args:
            media_buy_id: Campaign ID
            today: Current date

        Returns:
            Status response with campaign and line statuses
        """
        try:
            # Get campaign status
            campaign = self.campaigns.get_campaign(media_buy_id)
            campaign_status = YahooToAdCPStatusMapping.campaign(campaign.get("status", "UNKNOWN"))

            # Get lines
            lines = self.lines.list_lines(campaign_id=media_buy_id)

            package_statuses = []
            for line in lines:
                line_status = YahooToAdCPStatusMapping.line(line.get("status", "UNKNOWN"))
                package_statuses.append({
                    "package_id": str(line.get("id")),
                    "platform_line_item_id": str(line.get("id")),
                    "status": line_status,
                    "name": line.get("name", ""),
                })

            return CheckMediaBuyStatusResponse(
                media_buy_id=media_buy_id,
                status=campaign_status,
                packages=package_statuses,
            )

        except Exception as e:
            logger.error(f"Failed to check media buy status: {e}")
            return CheckMediaBuyStatusResponse(
                media_buy_id=media_buy_id,
                status="error",
                packages=[],
            )

    def get_media_buy_delivery(
        self,
        media_buy_id: str,
        date_range: ReportingPeriod,
        today: datetime,
    ) -> AdapterGetMediaBuyDeliveryResponse:
        """Get delivery data for a media buy.

        Args:
            media_buy_id: Campaign ID
            date_range: Reporting period
            today: Current date

        Returns:
            Delivery metrics for the campaign
        """
        try:
            # Parse date range
            start_date = date_range.start_date
            end_date = date_range.end_date

            # Get lines for package IDs
            lines = self.lines.list_lines(campaign_id=media_buy_id)
            line_ids = [str(line.get("id")) for line in lines]

            # Get delivery data
            delivery_data = self.reporting.get_delivery_for_adcp(
                campaign_id=media_buy_id,
                line_ids=line_ids,
                start_date=start_date,
                end_date=end_date,
            )

            # Format response
            totals = delivery_data.get("totals", {})

            return AdapterGetMediaBuyDeliveryResponse(
                media_buy_id=media_buy_id,
                totals=DeliveryTotals(
                    impressions=totals.get("impressions", 0),
                    clicks=totals.get("clicks", 0),
                    spend=totals.get("spend", 0),
                    conversions=totals.get("conversions", 0),
                ),
                packages=delivery_data.get("packages", []),
            )

        except Exception as e:
            logger.error(f"Failed to get media buy delivery: {e}")
            return AdapterGetMediaBuyDeliveryResponse(
                media_buy_id=media_buy_id,
                totals=DeliveryTotals(impressions=0, clicks=0, spend=0),
                packages=[],
            )

    def update_media_buy_performance_index(
        self,
        media_buy_id: str,
        package_performance: list[PackagePerformance],
    ) -> bool:
        """Update performance index for packages.

        Args:
            media_buy_id: Campaign ID
            package_performance: List of package performance updates

        Returns:
            True if all updates succeeded
        """
        success = True

        for perf in package_performance:
            try:
                self.lines.update_performance_index(
                    line_id=perf.package_id,
                    performance_index=perf.performance_index,
                )
            except Exception as e:
                logger.error(f"Failed to update performance index for {perf.package_id}: {e}")
                success = False

        return success

    def update_media_buy(
        self,
        media_buy_id: str,
        buyer_ref: str,
        action: str,
        package_id: str | None,
        budget: int | None,
        today: datetime,
    ) -> UpdateMediaBuyResponse:
        """Update a media buy.

        Args:
            media_buy_id: Campaign ID
            buyer_ref: Buyer reference
            action: Update action (pause, resume, cancel, update_budget)
            package_id: Optional specific package to update
            budget: New budget (for update_budget action)
            today: Current date

        Returns:
            Update response
        """
        try:
            if action == "pause":
                if package_id:
                    self.lines.pause_line(package_id)
                else:
                    self.campaigns.pause_campaign(media_buy_id)

            elif action == "resume":
                if package_id:
                    self.lines.activate_line(package_id)
                else:
                    self.campaigns.activate_campaign(media_buy_id)

            elif action == "cancel":
                self.campaigns.delete_campaign(media_buy_id)

            elif action == "update_budget" and budget is not None:
                if package_id:
                    self.lines.update_line(package_id, budget=budget)
                else:
                    self.campaigns.update_campaign(media_buy_id, budget=budget)

            else:
                return UpdateMediaBuyResponse(
                    error=UpdateMediaBuyError(
                        error=Error(
                            code="INVALID_ACTION",
                            message=f"Unknown action: {action}",
                        )
                    )
                )

            return UpdateMediaBuyResponse(
                success=UpdateMediaBuySuccess(
                    media_buy_id=media_buy_id,
                    buyer_ref=buyer_ref,
                    status="updated",
                    message=f"Successfully applied action: {action}",
                )
            )

        except Exception as e:
            logger.error(f"Failed to update media buy: {e}")
            return UpdateMediaBuyResponse(
                error=UpdateMediaBuyError(
                    error=Error(
                        code="UPDATE_FAILED",
                        message=str(e),
                    )
                )
            )

    def _determine_media_type(self, package: MediaPackage) -> str:
        """Determine Yahoo DSP media type from package.

        Args:
            package: Media package

        Returns:
            Yahoo DSP media type string
        """
        # Check creative format or package configuration
        if hasattr(package, "creative_format"):
            fmt = package.creative_format.lower() if package.creative_format else ""
            if "video" in fmt:
                return "VIDEO"
            elif "audio" in fmt:
                return "AUDIO"
            elif "native" in fmt:
                return "NATIVE"
            elif "ctv" in fmt:
                return "CTV"

        # Default to DISPLAY
        return "DISPLAY"

    def _build_targeting(self, package: MediaPackage) -> dict[str, Any]:
        """Build targeting specification for Yahoo DSP.

        Args:
            package: Media package with targeting

        Returns:
            Yahoo DSP targeting object
        """
        targeting = {}

        # Geographic targeting
        if hasattr(package, "geo_any_of") and package.geo_any_of:
            targeting["geo_any_of"] = package.geo_any_of

        # Device targeting
        if hasattr(package, "device_type_any_of") and package.device_type_any_of:
            targeting["device_type_any_of"] = package.device_type_any_of

        # Audience segments
        if hasattr(package, "audience_segment_ids") and package.audience_segment_ids:
            targeting["audience_segment_ids"] = package.audience_segment_ids

        return targeting

    def test_connection(self) -> tuple[bool, str]:
        """Test connection to Yahoo DSP API.

        Returns:
            Tuple of (success, message)
        """
        # First test auth
        auth_success, auth_message = self.auth_manager.test_connection()
        if not auth_success:
            return False, f"Authentication failed: {auth_message}"

        # Then test API
        return self.client.test_connection()
