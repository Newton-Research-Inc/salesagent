"""
Yahoo DSP Adapter - Simulates Programmatic Buying Experience

This adapter simulates a Demand-Side Platform (DSP) buying experience,
aligned with the Yahoo DSP API (https://help.yahooinc.com/dsp-api/docs/dsp-api-help-home).

Yahoo DSP Object Hierarchy:
- Advertiser → Campaign (Order) → Line → Ad

Key Features:
- Auction-based pricing (bid floors instead of fixed rates)
- Rich audience targeting (segments, behavioral, contextual)
- Real-time bidding simulation
- Campaign optimization (auto-bidding, pacing)
- Performance-focused reporting (CTR, conversions, win rates)
- Deal/PMP support for premium inventory
- Multiple exchange support

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
    
    Aligned with Yahoo DSP API terminology:
    - Campaign = Order (contains multiple Lines)
    - Line = Ad Group (targeting + budget + bidding)
    - Ad = Creative assignment
    
    Designed to showcase DSP-specific features:
    - Audience targeting (segments, lookalikes, retargeting)
    - Bid strategies (AUTOBID, MAXBID)
    - Supply path optimization (multiple exchanges)
    - Deal/PMP support
    - Real-time performance tracking
    """

    adapter_name = "yahoo_dsp"
    
    # In-memory storage for campaigns (simulates DSP state)
    _campaigns: dict[str, dict[str, Any]] = {}

    # =========================================================================
    # Yahoo DSP Status Values (from API documentation)
    # https://help.yahooinc.com/dsp-api/docs/lines
    # =========================================================================
    LINE_STATUSES = {
        "ACTIVE": "Active/running - Line is delivering",
        "PAUSED": "Paused by user - Temporarily stopped",
        "INACTIVE": "Inactive/ended - Manually deactivated",
        "STOP_TOTAL_BUDGET": "Total budget reached - Increase budget to resume",
        "STOP_DAILY_BUDGET": "Daily budget reached - Will resume tomorrow",
        "NOT_STARTED": "Not started yet - Before flight start date",
        "ENDED": "Ended - Flight dates have passed",
        "ERROR": "Error - Configuration issue",
        "ARCHIVED": "Archived - Campaign has been archived",
        "PENDING_REVIEW": "Pending review - Awaiting approval",
    }

    # =========================================================================
    # Yahoo DSP Media Types (immutable after Line creation)
    # =========================================================================
    MEDIA_TYPES = {
        "DISPLAY": "Display/banner ads",
        "VIDEO": "Video ads (pre-roll, mid-roll, etc.)",
        "AUDIO": "Audio ads (streaming, podcast)",
        "NATIVE": "Native ads",
    }

    # =========================================================================
    # Yahoo DSP Bidding Configuration
    # =========================================================================
    BID_STRATEGIES = {
        "AUTOBID": "Automatic bidding - DSP optimizes bids",
        "MAXBID": "Maximum bid - Set ceiling price",
    }

    BID_TYPES = {
        "DYNAMIC": "Dynamic bidding based on optimization",
        "FIXED": "Fixed bid amount",
    }

    GOAL_TYPES = {
        "IMPRESSION": "Optimize for impressions",
        "CLICK": "Optimize for clicks (CTR)",
        "CONVERSION": "Optimize for conversions (CPA)",
        "VIEWABLE_IMPRESSION": "Optimize for viewable impressions",
        "VIDEO_COMPLETION": "Optimize for video completions",
    }

    PACING_TYPES = {
        "EVEN": "Spread budget evenly across flight",
        "ACCELERATED": "Spend budget as fast as possible",
    }

    # =========================================================================
    # Yahoo DSP Exchanges (Supply Sources)
    # =========================================================================
    EXCHANGES = {
        "YAHOO_EXCHANGE": {
            "id": 1,
            "name": "Yahoo Exchange",
            "type": "owned",
            "description": "Yahoo-owned properties (Yahoo Mail, Yahoo Finance, etc.)",
        },
        "VERIZON_MEDIA": {
            "id": 2,
            "name": "Verizon Media",
            "type": "owned",
            "description": "Verizon Media properties",
        },
        "MAGNITE": {
            "id": 3,
            "name": "Magnite (Rubicon)",
            "type": "ssp",
            "description": "Premium publisher inventory via Magnite",
        },
        "PUBMATIC": {
            "id": 4,
            "name": "PubMatic",
            "type": "ssp",
            "description": "PubMatic exchange inventory",
        },
        "INDEX_EXCHANGE": {
            "id": 5,
            "name": "Index Exchange",
            "type": "ssp",
            "description": "Index Exchange inventory",
        },
        "OPEN_EXCHANGE": {
            "id": 99,
            "name": "Open RTB Marketplace",
            "type": "open",
            "description": "Open marketplace inventory",
        },
    }

    # =========================================================================
    # Yahoo DSP Deal Types (PMP Support)
    # =========================================================================
    DEAL_TYPES = {
        "PRIVATE_AUCTION": {
            "name": "Private Auction",
            "description": "Invitation-only auction with floor price",
            "guaranteed": False,
        },
        "PREFERRED_DEAL": {
            "name": "Preferred Deal",
            "description": "Fixed price, non-guaranteed access",
            "guaranteed": False,
        },
        "PROGRAMMATIC_GUARANTEED": {
            "name": "Programmatic Guaranteed",
            "description": "Fixed price, guaranteed delivery",
            "guaranteed": True,
        },
    }

    # =========================================================================
    # Yahoo DSP Audience Segment Types
    # =========================================================================
    AUDIENCE_TYPES = {
        "FIRST_PARTY": "Advertiser's own data (CRM, site visitors)",
        "THIRD_PARTY": "Data provider segments (Oracle, Experian)",
        "YAHOO_OWNED": "Yahoo behavioral data",
        "LOOKALIKE": "Modeled audiences based on seed",
        "RETARGETING": "Site/app visitor retargeting",
    }

    # DSP-specific: Supported audience segments with realistic metadata
    SUPPORTED_AUDIENCE_SEGMENTS = {
        "outdoor_enthusiasts": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 3500000,
            "cpm_lift": 0.25,
            "recency": "30_DAYS",
        },
        "eco_conscious_consumers": {
            "type": "THIRD_PARTY",
            "provider": "Oracle Data Cloud",
            "reach": 2800000,
            "cpm_lift": 0.30,
            "recency": "60_DAYS",
        },
        "sustainable_shoppers": {
            "type": "THIRD_PARTY",
            "provider": "Experian",
            "reach": 1500000,
            "cpm_lift": 0.35,
            "recency": "30_DAYS",
        },
        "adventure_travelers": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 1900000,
            "cpm_lift": 0.28,
            "recency": "45_DAYS",
        },
        "auto_intenders": {
            "type": "THIRD_PARTY",
            "provider": "Oracle Data Cloud",
            "reach": 5000000,
            "cpm_lift": 0.40,
            "recency": "14_DAYS",
        },
        "high_income_households": {
            "type": "THIRD_PARTY",
            "provider": "Experian",
            "reach": 4200000,
            "cpm_lift": 0.35,
            "recency": "90_DAYS",
        },
        "recent_purchasers": {
            "type": "FIRST_PARTY",
            "provider": "Advertiser",
            "reach": 500000,
            "cpm_lift": 0.50,
            "recency": "7_DAYS",
        },
        "travel_enthusiasts": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 3200000,
            "cpm_lift": 0.22,
            "recency": "30_DAYS",
        },
        "tech_early_adopters": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 2100000,
            "cpm_lift": 0.32,
            "recency": "30_DAYS",
        },
        "luxury_shoppers": {
            "type": "THIRD_PARTY",
            "provider": "Mastercard",
            "reach": 1800000,
            "cpm_lift": 0.45,
            "recency": "60_DAYS",
        },
        "fitness_enthusiasts": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 4500000,
            "cpm_lift": 0.20,
            "recency": "30_DAYS",
        },
        "home_improvement": {
            "type": "THIRD_PARTY",
            "provider": "Oracle Data Cloud",
            "reach": 3800000,
            "cpm_lift": 0.25,
            "recency": "45_DAYS",
        },
        "pet_owners": {
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 2900000,
            "cpm_lift": 0.18,
            "recency": "60_DAYS",
        },
        "parents_young_children": {
            "type": "THIRD_PARTY",
            "provider": "Experian",
            "reach": 2200000,
            "cpm_lift": 0.28,
            "recency": "90_DAYS",
        },
    }

    # DSP targeting support (broader than publisher ad servers)
    SUPPORTED_DEVICE_TYPES = {"mobile", "desktop", "tablet", "ctv", "dooh"}
    SUPPORTED_MEDIA_TYPES = {"video", "display", "native", "audio"}

    # =========================================================================
    # Frequency Cap Configuration (Yahoo DSP style)
    # =========================================================================
    FREQUENCY_CAP_DURATION_UNITS = ["HOUR", "DAY", "WEEK", "MONTH", "LIFETIME"]
    FREQUENCY_CAP_SCOPES = ["LINE", "CAMPAIGN", "ADVERTISER"]

    def __init__(self, config, principal, dry_run=False, creative_engine=None, tenant_id=None):
        """Initialize Yahoo DSP adapter."""
        super().__init__(config, principal, dry_run, creative_engine, tenant_id)
        
        # DSP-specific configuration
        self.default_bid_strategy = config.get("default_bid_strategy", "AUTOBID")
        self.default_goal_type = config.get("default_goal_type", "IMPRESSION")
        self.enable_auto_optimization = config.get("enable_auto_optimization", True)
        self.min_bid_floor = config.get("min_bid_floor", 0.50)  # $0.50 minimum bid
        self.max_bid_cap = config.get("max_bid_cap", 50.00)  # $50 maximum bid
        
        # Default exchanges to target
        self.default_exchanges = config.get(
            "default_exchanges", 
            ["YAHOO_EXCHANGE", "INDEX_EXCHANGE", "OPEN_EXCHANGE"]
        )

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
        """
        Map AdCP audience to Yahoo DSP segment with realistic metadata.
        
        Returns segment info matching Yahoo DSP API structure.
        """
        segment_config = self.SUPPORTED_AUDIENCE_SEGMENTS.get(audience_name)
        if segment_config:
            return {
                "id": f"seg_{hash(audience_name) % 100000}",
                "name": audience_name.replace("_", " ").title(),
                "type": segment_config["type"],
                "provider": segment_config["provider"],
                "reach": segment_config["reach"],
                "cpmLift": segment_config["cpm_lift"],
                "recency": segment_config["recency"],
                "qualityScore": random.uniform(0.75, 0.95),
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
            "excludedSegments": [],
            "lookalikeExpansion": False,
            "retargetingEnabled": False,
            "segmentOperator": "OR",  # OR = any segment, AND = all segments
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
                    audience_config["retargetingEnabled"] = True

        return audience_config

    def _configure_bidding(
        self, 
        strategy: str, 
        goal_type: str,
        max_bid: float,
        total_budget: float, 
        pacing: str = "EVEN"
    ) -> dict[str, Any]:
        """
        Configure DSP bidding strategy (Yahoo DSP API style).
        
        Yahoo DSP bidding fields:
        - bidStrategy: AUTOBID or MAXBID
        - bidType: DYNAMIC or FIXED
        - goalType: IMPRESSION, CLICK, CONVERSION, etc.
        - maxBid: Maximum CPM bid
        - pacingType: EVEN or ACCELERATED
        """
        config = {
            "bidStrategy": strategy,
            "bidType": "DYNAMIC" if strategy == "AUTOBID" else "FIXED",
            "goalType": goal_type,
            "maxBid": max_bid,
            "pacingType": pacing,
            "budgetAllocation": "DAILY_CAP",
        }

        # Add goal-specific configuration
        if goal_type == "CONVERSION":
            config["targetCpa"] = total_budget * 0.02  # 2% of budget per conversion
            config["learningPhaseDays"] = 7
        elif goal_type == "CLICK":
            config["targetCtr"] = 0.001  # 0.1% CTR target
        elif goal_type == "VIEWABLE_IMPRESSION":
            config["viewabilityTarget"] = 0.70  # 70% viewability target

        return config

    def _build_frequency_cap(
        self,
        limit: int = 3,
        duration: int = 1,
        duration_unit: str = "DAY",
        scope: str = "LINE",
    ) -> dict[str, Any]:
        """
        Build frequency cap configuration (Yahoo DSP style).
        
        Yahoo DSP frequency cap structure:
        - type: IMPRESSION or CLICK
        - limit: Max impressions/clicks
        - duration: Time period
        - durationUnit: DAY, WEEK, MONTH, LIFETIME
        - scope: LINE, CAMPAIGN, ADVERTISER
        """
        return {
            "type": "IMPRESSION",
            "limit": limit,
            "duration": duration,
            "durationUnit": duration_unit,
            "scope": scope,
        }

    def _get_deal_info(self, product_id: str) -> dict[str, Any] | None:
        """
        Get deal information if product is a PMP deal.
        
        Returns deal configuration for private marketplace inventory.
        """
        # Check if product is a PMP deal (convention: product_id contains "pmp" or "deal")
        if "pmp" in product_id.lower() or "deal" in product_id.lower():
            return {
                "dealId": f"DEAL-{uuid.uuid4().hex[:8].upper()}",
                "dealType": "PREFERRED_DEAL",
                "exchangeId": "YAHOO_EXCHANGE",
                "publisherName": "Premium Publisher Network",
                "floorPrice": random.uniform(8.0, 15.0),
                "guaranteed": False,
            }
        return None

    def _estimate_reach(
        self, 
        audience_config: dict[str, Any], 
        geo_targeting: list[str] | None = None,
        exchanges: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Estimate campaign reach based on targeting.
        
        DSPs provide reach estimates before campaign launch.
        """
        # Base reach calculation
        base_reach = 10000000  # 10M default reach

        # Reduce reach based on audience targeting
        if audience_config.get("segments"):
            segment_reach = sum(seg["reach"] for seg in audience_config["segments"])
            base_reach = min(base_reach, segment_reach)

        # Reduce reach based on geo targeting
        if geo_targeting:
            base_reach = int(base_reach * 0.6)  # 60% of audience in target geo

        # Adjust based on exchange selection
        if exchanges:
            exchange_multiplier = len(exchanges) / len(self.EXCHANGES)
            base_reach = int(base_reach * max(0.3, exchange_multiplier))

        return {
            "estimatedUniqueUsers": base_reach,
            "estimatedImpressions": int(base_reach * 3.5),  # 3.5 impressions per user
            "estimatedDailyImpressions": int(base_reach * 3.5 / 30),  # Assume 30-day campaign
            "confidence": random.uniform(0.75, 0.95),
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
            "medianWinningBid": round(base_bid * 1.05, 2),
            "percentile25": round(base_bid * 0.80, 2),
            "percentile75": round(base_bid * 1.25, 2),
            "percentile90": round(base_bid * 1.50, 2),
            "competitionLevel": random.choice(["LOW", "MEDIUM", "HIGH"]),
            "estimatedWinRateAtBid": {
                f"${round(base_bid * 0.80, 2)}": 0.25,
                f"${round(base_bid, 2)}": 0.45,
                f"${round(base_bid * 1.20, 2)}": 0.65,
                f"${round(base_bid * 1.50, 2)}": 0.85,
            },
        }

    def _determine_line_status(self, line: dict[str, Any], campaign: dict[str, Any]) -> str:
        """
        Determine the current status of a Line based on Yahoo DSP status logic.
        
        Status precedence:
        1. ARCHIVED - Campaign archived
        2. ERROR - Configuration error
        3. STOP_TOTAL_BUDGET - Budget exhausted
        4. STOP_DAILY_BUDGET - Daily budget reached
        5. ENDED - Flight dates passed
        6. NOT_STARTED - Before start date
        7. PAUSED - User paused
        8. INACTIVE - User deactivated
        9. PENDING_REVIEW - Awaiting approval
        10. ACTIVE - Delivering
        """
        now = datetime.now(UTC)
        
        # Check if campaign is archived
        if campaign.get("archived", False):
            return "ARCHIVED"
        
        # Check for errors
        if line.get("hasError", False):
            return "ERROR"
        
        # Check budget status
        spend = line.get("spend", 0)
        total_budget = line.get("scheduleBudget", 0)
        daily_budget = line.get("dailyBudget", 0)
        daily_spend = line.get("dailySpend", 0)
        
        if total_budget > 0 and spend >= total_budget:
            return "STOP_TOTAL_BUDGET"
        
        if daily_budget > 0 and daily_spend >= daily_budget:
            return "STOP_DAILY_BUDGET"
        
        # Check flight dates
        start_date = campaign.get("start_time")
        end_date = campaign.get("end_time")
        
        if end_date and now > end_date:
            return "ENDED"
        
        if start_date and now < start_date:
            return "NOT_STARTED"
        
        # Check user-set status
        user_status = line.get("userStatus", "ACTIVE")
        if user_status == "PAUSED":
            return "PAUSED"
        if user_status == "INACTIVE":
            return "INACTIVE"
        
        # Check if pending review
        if line.get("pendingReview", False):
            return "PENDING_REVIEW"
        
        return "ACTIVE"

    def create_media_buy(
        self,
        request: CreateMediaBuyRequest,
        packages: list[MediaPackage],
        start_time: datetime,
        end_time: datetime,
        package_pricing_info: dict[str, dict] | None = None,
    ) -> CreateMediaBuyResponse:
        """
        Create a DSP campaign with Lines (Yahoo DSP terminology).
        
        Yahoo DSP Object Mapping:
        - Media Buy → Campaign (Order)
        - Package → Line (targeting + budget + bidding)
        - Creative → Ad
        
        Line Object Fields (from Yahoo DSP API):
        - id, name, orderId (campaign), packageId
        - mediaType: DISPLAY, VIDEO, AUDIO
        - status: ACTIVE, PAUSED, INACTIVE, etc.
        - startDate, endDate
        - scheduleBudget, dailyBudget
        - bidStrategy, maxBid, goalType
        - frequencyCap
        """
        brand_name = request.brand_manifest.name if request.brand_manifest else "advertiser"
        self.log(f"🎯 Yahoo DSP: Creating campaign for {brand_name}")

        # Validate targeting
        unsupported_features = self._validate_targeting(request.targeting_overlay)
        if unsupported_features:
            raise ValueError(
                f"Unsupported targeting features for Yahoo DSP: {'; '.join(unsupported_features)}"
            )

        # Generate campaign ID (Yahoo DSP uses numeric IDs, we simulate with hash)
        campaign_id = f"yahoo_dsp_{uuid.uuid4().hex[:12]}"
        order_id = random.randint(100000, 999999)  # Yahoo DSP orderId

        # Build audience targeting
        audience_config = self._build_audience_targeting(request.targeting_overlay)
        
        # Estimate reach
        geo_targeting = request.targeting_overlay.geo_country_any_of if request.targeting_overlay else None
        reach_estimate = self._estimate_reach(
            audience_config, 
            geo_targeting,
            self.default_exchanges,
        )

        # Configure bidding strategy
        total_budget = sum(pkg.budget for pkg in packages)
        
        # Generate bid landscape
        bid_landscape = self._generate_bid_landscape(package_pricing_info)

        # Calculate campaign duration for daily budget
        campaign_days = max(1, (end_time - start_time).days)

        # Create Lines (Yahoo DSP equivalent of packages/ad groups)
        lines = []
        for pkg in packages:
            line_id = random.randint(1000000, 9999999)  # Yahoo DSP line ID
            
            # Get pricing info
            pricing = package_pricing_info.get(pkg.package_id, {}) if package_pricing_info else {}
            max_bid = pricing.get("rate", 8.00)
            
            # Determine media type from product
            media_type = "DISPLAY"  # Default
            if "video" in pkg.product_id.lower():
                media_type = "VIDEO"
            elif "audio" in pkg.product_id.lower():
                media_type = "AUDIO"
            elif "native" in pkg.product_id.lower():
                media_type = "NATIVE"

            # Check for deal/PMP
            deal_info = self._get_deal_info(pkg.product_id)

            # Build bidding configuration
            bidding_config = self._configure_bidding(
                strategy=self.default_bid_strategy,
                goal_type=self.default_goal_type,
                max_bid=max_bid,
                total_budget=pkg.budget,
                pacing="EVEN",
            )

            # Build frequency cap
            frequency_cap = self._build_frequency_cap(
                limit=3,
                duration=1,
                duration_unit="DAY",
                scope="LINE",
            )

            # Calculate daily budget
            daily_budget = round(pkg.budget / campaign_days, 2)

            line = {
                # Yahoo DSP Line object fields
                "id": line_id,
                "name": f"{brand_name} - {pkg.package_id}",
                "orderId": order_id,  # Campaign/Order ID
                "packageId": pkg.package_id,  # AdCP package reference
                "productId": pkg.product_id,
                
                # Media and status
                "mediaType": media_type,
                "status": "PENDING_REVIEW",  # Initial status
                "userStatus": "ACTIVE",  # User-set status
                "pendingReview": True,
                
                # Dates
                "startDate": start_time.strftime("%Y-%m-%d"),
                "endDate": end_time.strftime("%Y-%m-%d"),
                
                # Budget
                "scheduleBudget": pkg.budget,
                "dailyBudget": daily_budget,
                "spend": 0,
                "dailySpend": 0,
                
                # Bidding
                "bidStrategy": bidding_config["bidStrategy"],
                "bidType": bidding_config["bidType"],
                "goalType": bidding_config["goalType"],
                "maxBid": max_bid,
                "pacingType": bidding_config["pacingType"],
                
                # Targeting
                "frequencyCap": frequency_cap,
                "exchanges": self.default_exchanges,
                "audienceSegments": audience_config["segments"],
                
                # Deal info (if PMP)
                "deal": deal_info,
                
                # Creatives
                "creativeIds": pkg.creative_ids,
                "adIds": [],  # Will be populated when ads are created
            }
            
            lines.append(line)

        # Store campaign state
        self._campaigns[campaign_id] = {
            "campaignId": campaign_id,
            "orderId": order_id,
            "buyerRef": request.buyer_ref,
            "brandName": brand_name,
            "startTime": start_time,
            "endTime": end_time,
            "totalBudget": total_budget,
            "lines": lines,
            "audienceConfig": audience_config,
            "reachEstimate": reach_estimate,
            "bidLandscape": bid_landscape,
            "status": "PENDING_REVIEW",
            "archived": False,
            "createdAt": datetime.now(UTC),
        }

        self.log(f"✅ Yahoo DSP campaign created: {campaign_id}")
        self.log(f"   📋 Order ID: {order_id}")
        self.log(f"   📊 Estimated reach: {reach_estimate['estimatedUniqueUsers']:,} users")
        self.log(f"   💰 Total budget: ${total_budget:,.2f}")
        self.log(f"   📝 Lines: {len(lines)}")
        if audience_config["segments"]:
            self.log(f"   👥 Audience segments: {len(audience_config['segments'])}")
            for seg in audience_config["segments"][:3]:  # Show first 3
                self.log(f"      - {seg['name']} ({seg['type']}, {seg['reach']:,} reach)")

        # Build response packages (map Lines back to AdCP packages)
        response_packages = []
        for line in lines:
            response_packages.append(
                ResponsePackage(
                    package_id=line["packageId"],
                    status=PackageStatus.PENDING,  # Awaiting review
                    external_id=str(line["id"]),  # Yahoo DSP Line ID
                )
            )

        return CreateMediaBuySuccess(
            media_buy_id=campaign_id,
            status="pending",  # DSP status (not "active" immediately)
            external_ids={
                "yahoo_campaign_id": campaign_id,
                "yahoo_order_id": order_id,
                "line_ids": [line["id"] for line in lines],
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
        
        Yahoo DSP Reporting API metrics:
        - impressions, clicks, conversions, spend
        - ctr, cpm, cpc, cpa
        - viewableImpressions, viewabilityRate
        - winRate, bidRequests, bidsWon
        - videoCompletions, videoCompletionRate
        
        Dimensions available:
        - date, advertiser, campaign, line, ad
        - exchange, deal, device, geo, creative
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"📊 Yahoo DSP: Fetching performance for {media_buy_id}")

        # Simulate campaign performance for each Line
        packages = []
        for line in campaign["lines"]:
            # DSP metrics simulation
            max_bid = line["maxBid"]
            budget = line["scheduleBudget"]
            
            # Simulate auction participation
            bid_requests = random.randint(500000, 2000000)  # Total bid opportunities
            win_rate = random.uniform(0.25, 0.40)  # Won 25-40% of auctions
            impressions = int(bid_requests * win_rate)
            
            # Simulate performance metrics based on goal type
            goal_type = line.get("goalType", "IMPRESSION")
            
            if goal_type == "CLICK":
                # Higher CTR when optimizing for clicks
                ctr = random.uniform(0.0010, 0.0018)  # 0.10-0.18% CTR
            else:
                ctr = random.uniform(0.0008, 0.0012)  # 0.08-0.12% CTR
            
            clicks = int(impressions * ctr)
            
            # Conversions
            if goal_type == "CONVERSION":
                conversion_rate = random.uniform(0.025, 0.045)  # 2.5-4.5% conversion
            else:
                conversion_rate = random.uniform(0.018, 0.028)  # 1.8-2.8% conversion
            
            conversions = int(clicks * conversion_rate)
            
            # Calculate costs (DSP pricing is dynamic)
            avg_win_price = max_bid * random.uniform(0.85, 1.02)  # Win price near bid
            spend = (impressions / 1000) * avg_win_price
            
            # Update line spend tracking
            line["spend"] = spend
            line["dailySpend"] = spend / max(1, (campaign["endTime"] - campaign["startTime"]).days)
            
            # Viewability (DSP key metric)
            viewability_rate = random.uniform(0.68, 0.82)  # 68-82% viewable
            viewable_impressions = int(impressions * viewability_rate)
            
            # Determine current status
            status = self._determine_line_status(line, campaign)
            line["status"] = status
            
            # Map status to PackageStatus
            if status in ["ACTIVE"]:
                pkg_status = PackageStatus.DELIVERING
            elif status in ["PENDING_REVIEW", "NOT_STARTED"]:
                pkg_status = PackageStatus.PENDING
            elif status in ["ENDED", "STOP_TOTAL_BUDGET"]:
                pkg_status = PackageStatus.COMPLETED
            elif status in ["PAUSED", "INACTIVE", "STOP_DAILY_BUDGET"]:
                pkg_status = PackageStatus.PAUSED
            else:
                pkg_status = PackageStatus.PENDING

            packages.append(
                PackagePerformance(
                    package_id=line["packageId"],
                    external_id=str(line["id"]),
                    status=pkg_status,
                    impressions=impressions,
                    clicks=clicks,
                    spend=round(spend, 2),
                    
                    # DSP-specific metrics in metadata
                    metadata={
                        # Yahoo DSP Line info
                        "lineId": line["id"],
                        "lineName": line["name"],
                        "lineStatus": status,
                        "mediaType": line["mediaType"],
                        
                        # Bidding metrics
                        "bidRequests": bid_requests,
                        "bidsWon": impressions,
                        "winRate": round(win_rate, 3),
                        "avgBid": max_bid,
                        "avgWinPrice": round(avg_win_price, 2),
                        
                        # Performance metrics
                        "ctr": round(ctr, 5),
                        "conversions": conversions,
                        "conversionRate": round(conversion_rate, 4),
                        "cpm": round(avg_win_price, 2),
                        "cpc": round(spend / clicks if clicks > 0 else 0, 2),
                        "cpa": round(spend / conversions if conversions > 0 else 0, 2),
                        
                        # Viewability
                        "viewableImpressions": viewable_impressions,
                        "viewabilityRate": round(viewability_rate, 3),
                        
                        # Budget tracking
                        "scheduleBudget": line["scheduleBudget"],
                        "dailyBudget": line["dailyBudget"],
                        "budgetUtilization": round(spend / budget if budget > 0 else 0, 3),
                        
                        # Audience info
                        "audienceSegments": len(line.get("audienceSegments", [])),
                        
                        # Exchange breakdown (simulated)
                        "exchangeBreakdown": {
                            "YAHOO_EXCHANGE": round(impressions * 0.45),
                            "INDEX_EXCHANGE": round(impressions * 0.30),
                            "OPEN_EXCHANGE": round(impressions * 0.25),
                        },
                    },
                )
            )

        # Calculate totals
        total_impressions = sum(p.impressions for p in packages)
        total_clicks = sum(p.clicks for p in packages)
        total_spend = sum(p.spend for p in packages)
        total_conversions = sum(p.metadata.get("conversions", 0) for p in packages if p.metadata)

        self.log(f"   📈 Impressions: {total_impressions:,}")
        self.log(f"   🖱️  Clicks: {total_clicks:,}")
        self.log(f"   💰 Spend: ${total_spend:,.2f}")
        self.log(f"   🎯 Conversions: {total_conversions}")
        self.log(f"   📊 Avg Win Rate: {sum(p.metadata.get('winRate', 0) for p in packages if p.metadata) / len(packages):.1%}")

        return AdapterGetMediaBuyDeliveryResponse(
            packages=packages,
            totals=DeliveryTotals(
                impressions=total_impressions,
                clicks=total_clicks,
                spend=round(total_spend, 2),
            ),
        )

    def check_media_buy_status(self, media_buy_id: str) -> CheckMediaBuyStatusResponse:
        """Check DSP campaign status with Yahoo DSP status values."""
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            return CheckMediaBuyStatusResponse(
                media_buy_id=media_buy_id,
                status="not_found",
                packages=[],
            )

        # Determine overall campaign status from Lines
        line_statuses = []
        packages = []
        
        for line in campaign["lines"]:
            status = self._determine_line_status(line, campaign)
            line["status"] = status
            line_statuses.append(status)
            
            # Map to PackageStatus
            if status in ["ACTIVE"]:
                pkg_status = PackageStatus.DELIVERING
            elif status in ["PENDING_REVIEW", "NOT_STARTED"]:
                pkg_status = PackageStatus.PENDING
            elif status in ["ENDED", "STOP_TOTAL_BUDGET"]:
                pkg_status = PackageStatus.COMPLETED
            elif status in ["PAUSED", "INACTIVE", "STOP_DAILY_BUDGET"]:
                pkg_status = PackageStatus.PAUSED
            else:
                pkg_status = PackageStatus.PENDING
            
            packages.append(
                ResponsePackage(
                    package_id=line["packageId"],
                    status=pkg_status,
                    external_id=str(line["id"]),
                )
            )

        # Determine overall campaign status
        if all(s == "ENDED" for s in line_statuses):
            campaign_status = "completed"
        elif all(s in ["PAUSED", "INACTIVE"] for s in line_statuses):
            campaign_status = "paused"
        elif any(s == "ACTIVE" for s in line_statuses):
            campaign_status = "active"
        elif any(s == "PENDING_REVIEW" for s in line_statuses):
            campaign_status = "pending_review"
        else:
            campaign_status = line_statuses[0].lower() if line_statuses else "unknown"

        return CheckMediaBuyStatusResponse(
            media_buy_id=media_buy_id,
            status=campaign_status,
            packages=packages,
        )

    def update_media_buy(
        self,
        media_buy_id: str,
        updates: dict[str, Any],
    ) -> UpdateMediaBuyResponse:
        """
        Update DSP campaign/Lines.
        
        Yahoo DSP update restrictions:
        - Cannot change mediaType after Line creation
        - Cannot change dates significantly after launch
        - Can update: budget, maxBid, status, frequencyCap
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"🔄 Yahoo DSP: Updating campaign {media_buy_id}")

        # Allowed updates for Lines
        allowed_line_updates = {
            "scheduleBudget", "dailyBudget", "maxBid", 
            "userStatus", "frequencyCap", "pacingType"
        }
        
        # Immutable fields
        immutable_fields = {"mediaType", "orderId", "id"}

        changes = []
        for key, value in updates.items():
            if key in immutable_fields:
                self.log(f"   ⚠️  Cannot update {key} (immutable after creation)")
                continue
            
            if key in allowed_line_updates:
                # Update all Lines
                for line in campaign["lines"]:
                    line[key] = value
                changes.append(f"{key}: {value}")
                self.log(f"   ✓ Updated {key}: {value}")
            elif key == "status":
                # Map status to userStatus
                if value.upper() in ["ACTIVE", "PAUSED", "INACTIVE"]:
                    for line in campaign["lines"]:
                        line["userStatus"] = value.upper()
                        line["pendingReview"] = False
                    changes.append(f"userStatus: {value.upper()}")
                    self.log(f"   ✓ Updated userStatus: {value.upper()}")
            else:
                self.log(f"   ⚠️  Unknown field {key}")

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
        """
        Add creative assets (Ads) to DSP Line.
        
        Yahoo DSP Ad object is created when creative is assigned to Line.
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            raise ValueError(f"Campaign {media_buy_id} not found in Yahoo DSP")

        self.log(f"🎨 Yahoo DSP: Adding {len(assets)} creatives to campaign {media_buy_id}")

        # Find the target Line
        target_line = None
        for line in campaign["lines"]:
            if line["packageId"] == package_id:
                target_line = line
                break

        results = []
        for asset in assets:
            creative_id = asset.get("creative_id", f"creative_{uuid.uuid4().hex[:8]}")
            
            # Create Ad object (Yahoo DSP terminology)
            ad_id = random.randint(10000000, 99999999)
            
            # Simulate DSP creative review
            status = "PENDING_REVIEW"  # DSPs review creatives
            
            if target_line:
                target_line["adIds"].append(ad_id)
            
            results.append(
                AssetStatus(
                    creative_id=creative_id,
                    status=status,
                    external_id=str(ad_id),  # Yahoo DSP Ad ID
                )
            )
            self.log(f"   ✓ Creative {creative_id} → Ad {ad_id}: {status}")

        return results
