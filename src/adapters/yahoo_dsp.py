"""
Yahoo DSP Adapter - Simulates Programmatic Buying Experience

This adapter simulates a Demand-Side Platform (DSP) buying experience,
focusing on programmatic features like:
- Auction-based pricing (bid floors instead of fixed rates)
- Rich audience targeting (segments, behavioral, contextual)
- Real-time bidding simulation
- Campaign optimization (auto-bidding, pacing)
- Performance-focused reporting (CTR, conversions, win rates)

Key Differences from Publisher Adapters (GAM/Mock):
- Inventory: Access to external supply (exchanges) vs owned ad units
- Buying: Programmatic/RTB vs direct deals
- Targeting: Audience-first vs placement-first
- Pricing: Bid-based vs fixed CPM
- Optimization: Real-time bidding algorithms vs delivery pacing
"""

import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from adcp.types import PackageStatus
from adcp.types.aliases import Package as ResponsePackage

from src.adapters.base import AdServerAdapter
from src.core.schemas import (
    AdapterGetMediaBuyDeliveryResponse,
    AssetStatus,
    CheckMediaBuyStatusResponse,
    CreateMediaBuyRequest,
    CreateMediaBuyResponse,
    CreateMediaBuySuccess,
    DeliveryTotals,
    MediaPackage,
    PackagePerformance,
    ReportingPeriod,
    UpdateMediaBuyResponse,
    UpdateMediaBuySuccess,
)


class YahooDSP(AdServerAdapter):
    """
    Yahoo DSP adapter - simulates programmatic buying experience.
    
    Designed to showcase DSP-specific features:
    - Audience targeting (segments, lookalikes, retargeting)
    - Bid strategies (manual, auto-optimize)
    - Supply path optimization
    - Real-time performance tracking
    """

    adapter_name = "yahoo_dsp"
    
    # In-memory storage for campaigns (simulates DSP state)
    _campaigns: dict[str, dict[str, Any]] = {}

    # DSP-specific: Supported audience segments
    SUPPORTED_AUDIENCE_SEGMENTS = {
        "auto_intenders",
        "high_income_households",
        "recent_purchasers",
        "travel_enthusiasts",
        "tech_early_adopters",
        "luxury_shoppers",
        "fitness_enthusiasts",
        "home_improvement",
        "pet_owners",
        "parents_young_children",
    }

    # DSP-specific: Bidding strategies
    SUPPORTED_BIDDING_STRATEGIES = {
        "manual_cpm": "Set a fixed CPM bid",
        "auto_optimize_ctr": "Automatically optimize bids for click-through rate",
        "auto_optimize_cpa": "Optimize for cost per acquisition",
        "maximize_reach": "Maximize unique users reached",
        "target_frequency": "Target specific frequency cap",
    }

    # DSP-specific: Inventory sources (exchanges)
    INVENTORY_SOURCES = {
        "yahoo_exchange": "Yahoo-owned properties",
        "verizon_media": "Verizon Media properties",
        "open_exchange": "Open marketplace inventory",
        "premium_pmps": "Private marketplace deals",
    }

    # DSP targeting support (broader than publisher ad servers)
    SUPPORTED_DEVICE_TYPES = {"mobile", "desktop", "tablet", "ctv", "dooh"}
    SUPPORTED_MEDIA_TYPES = {"video", "display", "native", "audio"}

    def __init__(self, config, principal, dry_run=False, creative_engine=None, tenant_id=None):
        """Initialize Yahoo DSP adapter."""
        super().__init__(config, principal, dry_run, creative_engine, tenant_id)
        
        # DSP-specific configuration
        self.default_bidding_strategy = config.get("default_bidding_strategy", "manual_cpm")
        self.enable_auto_optimization = config.get("enable_auto_optimization", True)
        self.min_bid_floor = config.get("min_bid_floor", 0.50)  # $0.50 minimum bid
        self.max_bid_cap = config.get("max_bid_cap", 50.00)  # $50 maximum bid

    def get_supported_pricing_models(self) -> set[str]:
        """Yahoo DSP supports programmatic pricing models."""
        return {"cpm", "cpc", "cpcv", "cpa"}  # No flat_rate (programmatic only)

    def _validate_targeting(self, targeting_overlay):
        """Validate DSP targeting - DSPs support rich targeting."""
        unsupported = []

        # DSPs SUPPORT audience targeting (unlike basic publisher servers)
        # No validation needed for audiences_any_of

        # DSPs SUPPORT device targeting
        if targeting_overlay and targeting_overlay.device_type_any_of:
            for device in targeting_overlay.device_type_any_of:
                if device not in self.SUPPORTED_DEVICE_TYPES:
                    unsupported.append(f"Device type '{device}' not supported by Yahoo DSP")

        return unsupported

    def _map_audience_to_segment(self, audience_name: str) -> dict[str, Any] | None:
        """Map AdCP audience to Yahoo DSP segment with reach and CPM lift data."""
        # Simulate segment lookup with realistic DSP data
        if audience_name in self.SUPPORTED_AUDIENCE_SEGMENTS:
            return {
                "id": f"yahoo_seg_{uuid.uuid4().hex[:8]}",
                "name": audience_name,
                "reach": random.randint(100000, 10000000),  # 100K - 10M users
                "cpm_lift": random.uniform(0.15, 0.50),  # 15-50% CPM increase for targeting
                "quality_score": random.uniform(0.7, 0.95),  # Segment quality (0-1)
            }
        return None

    def _build_audience_targeting(self, targeting_overlay) -> dict[str, Any]:
        """
        Build DSP audience targeting configuration.
        
        DSPs excel at audience targeting beyond basic geo/device:
        - First-party data (advertiser's CRM lists)
        - Third-party segments (data providers)
        - Lookalike modeling
        - Retargeting pools
        """
        audience_config = {
            "segments": [],
            "excluded_segments": [],
            "lookalike_expansion": False,
            "retargeting_enabled": False,
        }

        if not targeting_overlay:
            return audience_config

        # Map AdCP audiences to Yahoo DSP segments
        if targeting_overlay.audiences_any_of:
            for audience in targeting_overlay.audiences_any_of:
                segment = self._map_audience_to_segment(audience)
                if segment:
                    audience_config["segments"].append(segment)

        # Check for retargeting pools in signals
        if targeting_overlay.signals:
            for signal in targeting_overlay.signals:
                if "retargeting" in signal.lower() or "remarketing" in signal.lower():
                    audience_config["retargeting_enabled"] = True

        return audience_config

    def _configure_bidding(
        self, strategy: str, total_budget: float, pacing: str = "even"
    ) -> dict[str, Any]:
        """
        Configure DSP bidding strategy.
        
        DSPs use sophisticated bidding algorithms:
        - Manual CPM: Fixed bid amount
        - Auto-optimize CTR: Machine learning optimizes for clicks
        - Auto-optimize CPA: Optimize for conversions
        - Maximize reach: Bid to reach most unique users
        """
        base_config = {
            "strategy": strategy,
            "pacing": pacing,  # "even" vs "accelerated"
            "budget_allocation": "daily_cap",  # vs "lifetime_cap"
        }

        if strategy == "manual_cpm":
            # Fixed CPM bidding
            base_config.update({
                "goal": "impressions",
                "bid_type": "fixed",
                "optimization": None,
            })
        elif strategy == "auto_optimize_ctr":
            # Optimize for clicks
            base_config.update({
                "goal": "maximize_clicks",
                "bid_type": "dynamic",
                "target_ctr": 0.10,  # 0.10% CTR target
                "bid_adjustments": {
                    "mobile": 1.2,  # 20% higher on mobile
                    "evening_hours": 1.15,  # 15% higher 6pm-10pm
                    "weekend": 0.90,  # 10% lower on weekends
                },
            })
        elif strategy == "auto_optimize_cpa":
            # Optimize for conversions
            base_config.update({
                "goal": "conversions",
                "bid_type": "dynamic",
                "target_cpa": total_budget * 0.05,  # 5% of budget per conversion
                "learning_phase_days": 7,  # 7 days to gather data
            })
        elif strategy == "maximize_reach":
            # Reach optimization
            base_config.update({
                "goal": "unique_reach",
                "bid_type": "dynamic",
                "frequency_cap": 3,  # Max 3 impressions per user
            })

        return base_config

    def _estimate_reach(self, audience_config: dict[str, Any], geo_targeting: list[str] | None = None) -> dict[str, Any]:
        """
        Estimate campaign reach based on targeting.
        
        DSPs provide reach estimates before campaign launch.
        """
        # Base reach calculation
        base_reach = 10000000  # 10M default reach

        # Reduce reach based on targeting
        if audience_config.get("segments"):
            # Audience targeting reduces reach but increases relevance
            segment_reach = sum(seg["reach"] for seg in audience_config["segments"])
            base_reach = min(base_reach, segment_reach)

        if geo_targeting:
            # Geo targeting further reduces reach
            base_reach = int(base_reach * 0.6)  # 60% of audience in target geo

        return {
            "estimated_unique_users": base_reach,
            "estimated_impressions": int(base_reach * 3.5),  # 3.5 impressions per user
            "confidence": random.uniform(0.75, 0.95),  # 75-95% confidence
        }

    def _generate_bid_landscape(self, package_pricing_info: dict[str, dict] | None) -> dict[str, Any]:
        """
        Generate bid landscape data (DSP-specific feature).
        
        Shows competitive bidding environment to help advertisers set bids.
        """
        if not package_pricing_info:
            return {}

        # Simulate bid landscape for first package
        first_package = list(package_pricing_info.values())[0] if package_pricing_info else {}
        base_bid = first_package.get("rate", 5.00)

        return {
            "median_winning_bid": base_bid * 1.05,
            "percentile_25": base_bid * 0.80,
            "percentile_75": base_bid * 1.25,
            "percentile_90": base_bid * 1.50,
            "competition_level": random.choice(["low", "medium", "high"]),
            "estimated_win_rate_at_bid": {
                str(base_bid * 0.80): 0.25,  # 25% win rate at 20% below median
                str(base_bid): 0.45,  # 45% win rate at median
                str(base_bid * 1.20): 0.65,  # 65% win rate at 20% above median
                str(base_bid * 1.50): 0.85,  # 85% win rate at 50% above median
            },
        }

    def create_media_buy(
        self,
        request: CreateMediaBuyRequest,
        packages: list[MediaPackage],
        start_time: datetime,
        end_time: datetime,
        package_pricing_info: dict[str, dict] | None = None,
    ) -> CreateMediaBuyResponse:
        """
        Create a DSP campaign.
        
        Maps AdCP concepts to DSP terminology:
        - Media Buy → Campaign
        - Packages → Ad Groups
        - Pricing → Bid Strategy
        """
        self.log(f"🎯 Yahoo DSP: Creating campaign for {request.brand_manifest.name if request.brand_manifest else 'advertiser'}")

        # Validate targeting
        unsupported_features = self._validate_targeting(request.targeting_overlay)
        if unsupported_features:
            raise ValueError(
                f"Unsupported targeting features for Yahoo DSP: {'; '.join(unsupported_features)}"
            )

        # Generate campaign ID
        campaign_id = f"yahoo_dsp_{uuid.uuid4().hex[:12]}"

        # Build audience targeting
        audience_config = self._build_audience_targeting(request.targeting_overlay)
        
        # Estimate reach
        geo_targeting = request.targeting_overlay.geo_country_any_of if request.targeting_overlay else None
        reach_estimate = self._estimate_reach(audience_config, geo_targeting)

        # Configure bidding strategy
        total_budget = sum(pkg.budget for pkg in packages)
        bidding_config = self._configure_bidding(
            strategy=self.default_bidding_strategy,
            total_budget=total_budget,
            pacing="even",
        )

        # Generate bid landscape
        bid_landscape = self._generate_bid_landscape(package_pricing_info)

        # Create ad groups (DSP equivalent of packages)
        ad_groups = []
        for pkg in packages:
            ad_group_id = f"adgroup_{uuid.uuid4().hex[:8]}"
            
            # Get pricing info
            pricing = package_pricing_info.get(pkg.package_id, {}) if package_pricing_info else {}
            bid_amount = pricing.get("rate", 5.00)

            ad_groups.append({
                "ad_group_id": ad_group_id,
                "package_id": pkg.package_id,
                "product_id": pkg.product_id,
                "budget": pkg.budget,
                "bid_amount": bid_amount,
                "creative_ids": pkg.creative_ids,
                "status": "pending_review",  # DSPs typically review campaigns
            })

        # Store campaign state
        self._campaigns[campaign_id] = {
            "campaign_id": campaign_id,
            "buyer_ref": request.buyer_ref,
            "brand_name": request.brand_manifest.name if request.brand_manifest else "Unknown",
            "start_time": start_time,
            "end_time": end_time,
            "total_budget": total_budget,
            "ad_groups": ad_groups,
            "audience_config": audience_config,
            "bidding_config": bidding_config,
            "reach_estimate": reach_estimate,
            "bid_landscape": bid_landscape,
            "status": "pending_review",  # DSP campaigns go through approval
            "created_at": datetime.now(UTC),
        }

        self.log(f"✅ Yahoo DSP campaign created: {campaign_id}")
        self.log(f"   📊 Estimated reach: {reach_estimate['estimated_unique_users']:,} users")
        self.log(f"   💰 Total budget: ${total_budget:,.2f}")
        self.log(f"   🎯 Ad groups: {len(ad_groups)}")
        if audience_config["segments"]:
            self.log(f"   👥 Audience segments: {len(audience_config['segments'])}")

        # Build response packages
        response_packages = []
        for ad_group in ad_groups:
            response_packages.append(
                ResponsePackage(
                    package_id=ad_group["package_id"],
                    status=PackageStatus.PENDING,  # Awaiting review
                    external_id=ad_group["ad_group_id"],
                )
            )

        return CreateMediaBuySuccess(
            media_buy_id=campaign_id,
            status="pending",  # DSP status (not "active" immediately)
            external_ids={
                "yahoo_campaign_id": campaign_id,
                "ad_group_ids": [ag["ad_group_id"] for ag in ad_groups],
            },
            packages=response_packages,
        )

    def get_media_buy_delivery(
        self,
        media_buy_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reporting_period: ReportingPeriod | None = None,
    ) -> AdapterGetMediaBuyDeliveryResponse:
        """
        Get DSP campaign performance with programmatic-specific metrics.
        
        DSP reporting includes:
        - Bid landscape analysis
        - Win rate metrics
        - Viewability scores
        - Post-click/view conversions
        - Audience performance breakdown
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"📊 Yahoo DSP: Fetching performance for {media_buy_id}")

        # Simulate campaign performance
        packages = []
        for ad_group in campaign["ad_groups"]:
            # DSP metrics simulation
            bid_amount = ad_group["bid_amount"]
            budget = ad_group["budget"]
            
            # Simulate auction participation
            bid_requests = random.randint(100000, 1000000)  # Total bid opportunities
            win_rate = random.uniform(0.20, 0.40)  # Won 20-40% of auctions
            impressions = int(bid_requests * win_rate)
            
            # Simulate performance metrics
            clicks = int(impressions * random.uniform(0.0008, 0.0015))  # 0.08-0.15% CTR
            conversions = int(clicks * random.uniform(0.02, 0.05))  # 2-5% conversion rate
            
            # Calculate costs (DSP pricing is dynamic)
            avg_win_price = bid_amount * random.uniform(0.85, 1.05)  # Win price near bid
            spend = (impressions / 1000) * avg_win_price
            
            # Viewability (DSP key metric)
            viewability_rate = random.uniform(0.65, 0.85)  # 65-85% viewable
            
            packages.append(
                PackagePerformance(
                    package_id=ad_group["package_id"],
                    external_id=ad_group["ad_group_id"],
                    status=PackageStatus.DELIVERING,
                    impressions=impressions,
                    clicks=clicks,
                    spend=spend,
                    
                    # DSP-specific metrics (not in base AdCP but allowed as extensions)
                    metadata={
                        "bid_requests": bid_requests,
                        "win_rate": round(win_rate, 3),
                        "avg_bid": bid_amount,
                        "avg_win_price": round(avg_win_price, 2),
                        "viewability_rate": round(viewability_rate, 3),
                        "conversions": conversions,
                        "conversion_rate": round(conversions / clicks if clicks > 0 else 0, 4),
                        "ctr": round(clicks / impressions if impressions > 0 else 0, 5),
                        "audience_segments": len(campaign.get("audience_config", {}).get("segments", [])),
                    },
                )
            )

        # Calculate totals
        total_impressions = sum(p.impressions for p in packages)
        total_clicks = sum(p.metadata.get("clicks", 0) for p in packages if p.metadata)
        total_spend = sum(p.spend for p in packages)
        total_conversions = sum(p.metadata.get("conversions", 0) for p in packages if p.metadata)

        self.log(f"   📈 Impressions: {total_impressions:,}")
        self.log(f"   🖱️  Clicks: {total_clicks:,}")
        self.log(f"   💰 Spend: ${total_spend:,.2f}")
        self.log(f"   🎯 Conversions: {total_conversions}")

        return AdapterGetMediaBuyDeliveryResponse(
            packages=packages,
            totals=DeliveryTotals(
                impressions=total_impressions,
                clicks=total_clicks,
                spend=total_spend,
            ),
        )

    def check_media_buy_status(self, media_buy_id: str) -> CheckMediaBuyStatusResponse:
        """Check DSP campaign status."""
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            return CheckMediaBuyStatusResponse(
                media_buy_id=media_buy_id,
                status="not_found",
                packages=[],
            )

        # Simulate campaign lifecycle
        # DSP campaigns: pending_review → active → delivering → completed
        current_status = campaign.get("status", "pending_review")
        
        packages = []
        for ad_group in campaign["ad_groups"]:
            packages.append(
                ResponsePackage(
                    package_id=ad_group["package_id"],
                    status=PackageStatus.PENDING if current_status == "pending_review" else PackageStatus.DELIVERING,
                    external_id=ad_group["ad_group_id"],
                )
            )

        return CheckMediaBuyStatusResponse(
            media_buy_id=media_buy_id,
            status=current_status,
            packages=packages,
        )

    def update_media_buy(
        self,
        media_buy_id: str,
        updates: dict[str, Any],
    ) -> UpdateMediaBuyResponse:
        """
        Update DSP campaign (limited compared to publisher servers).
        
        DSP campaigns typically have restrictions on what can be changed
        after launch due to auction dynamics.
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"🔄 Yahoo DSP: Updating campaign {media_buy_id}")

        # DSP restrictions: Can't change dates or fundamental targeting after launch
        allowed_updates = ["budget", "bid_amount", "status"]
        
        changes = []
        for key, value in updates.items():
            if key in allowed_updates:
                campaign[key] = value
                changes.append(f"{key}: {value}")
                self.log(f"   ✓ Updated {key}: {value}")
            else:
                self.log(f"   ⚠️  Cannot update {key} (DSP restriction)")

        return UpdateMediaBuySuccess(
            media_buy_id=media_buy_id,
            changes=changes,
        )

    def add_creative_assets(
        self,
        media_buy_id: str,
        package_id: str,
        assets: list[dict[str, Any]],
    ) -> list[AssetStatus]:
        """Add creative assets to DSP ad group."""
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"🎨 Yahoo DSP: Adding {len(assets)} creatives to campaign {media_buy_id}")

        results = []
        for asset in assets:
            creative_id = asset.get("creative_id", f"creative_{uuid.uuid4().hex[:8]}")
            
            # Simulate DSP creative review
            status = "pending_review"  # DSPs review creatives
            
            results.append(
                AssetStatus(
                    creative_id=creative_id,
                    status=status,
                    external_id=f"yahoo_creative_{creative_id}",
                )
            )
            self.log(f"   ✓ Creative {creative_id}: {status}")

        return results

