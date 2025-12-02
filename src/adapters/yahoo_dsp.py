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
    # Yahoo DSP Bidding Configuration (from Yahoo DSP API)
    # https://help.yahooinc.com/dsp-api/docs/lines
    # =========================================================================
    BID_STRATEGIES = {
        "AUTOBID": {
            "description": "Automatic bidding - DSP optimizes bids dynamically",
            "bidType": "DYNAMIC",
            "supportsLearningPhase": True,
            "supportsTargetMetrics": True,
        },
        "MAXBID": {
            "description": "Maximum bid - Fixed ceiling price for all auctions",
            "bidType": "FIXED",
            "supportsLearningPhase": False,
            "supportsTargetMetrics": False,
        },
    }

    BID_TYPES = {
        "DYNAMIC": "Dynamic bidding based on real-time optimization signals",
        "FIXED": "Fixed bid amount for all auctions",
    }

    # Goal types with associated metrics and learning requirements
    GOAL_TYPES = {
        "IMPRESSION": {
            "description": "Optimize for impressions (CPM)",
            "metric": "impressions",
            "learningPhaseDays": 0,
            "minDataPoints": 0,
        },
        "CLICK": {
            "description": "Optimize for clicks (CTR)",
            "metric": "clicks",
            "targetField": "targetCtr",
            "defaultTarget": 0.001,  # 0.1% CTR
            "learningPhaseDays": 3,
            "minDataPoints": 100,
        },
        "CONVERSION": {
            "description": "Optimize for conversions (CPA)",
            "metric": "conversions",
            "targetField": "targetCpa",
            "learningPhaseDays": 7,
            "minDataPoints": 50,
            "requiresPixel": True,
        },
        "VIEWABLE_IMPRESSION": {
            "description": "Optimize for viewable impressions (vCPM)",
            "metric": "viewableImpressions",
            "targetField": "viewabilityTarget",
            "defaultTarget": 0.70,  # 70% viewability
            "learningPhaseDays": 3,
            "minDataPoints": 1000,
        },
        "VIDEO_COMPLETION": {
            "description": "Optimize for video completions (CPCV)",
            "metric": "videoCompletions",
            "targetField": "targetCompletionRate",
            "defaultTarget": 0.70,  # 70% completion rate
            "learningPhaseDays": 5,
            "minDataPoints": 200,
            "mediaTypes": ["VIDEO"],
        },
    }

    PACING_TYPES = {
        "EVEN": {
            "description": "Spread budget evenly across flight",
            "algorithm": "time_weighted",
            "overspendAllowed": False,
        },
        "ACCELERATED": {
            "description": "Spend budget as fast as possible",
            "algorithm": "asap",
            "overspendAllowed": True,
        },
    }

    # =========================================================================
    # Yahoo DSP Exchanges (Supply Sources) - Enhanced with realistic metadata
    # https://help.yahooinc.com/dsp-api/docs/traffic-api
    # =========================================================================
    EXCHANGES = {
        "YAHOO_EXCHANGE": {
            "id": 1,
            "name": "Yahoo Exchange",
            "type": "owned",
            "description": "Yahoo-owned properties (Yahoo Mail, Yahoo Finance, Yahoo Sports, etc.)",
            "avgCpm": 6.50,
            "viewabilityRate": 0.72,
            "dailyImpressions": 500000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "NATIVE"],
            "geoAvailability": ["US", "CA", "UK", "AU", "DE", "FR", "JP"],
            "brandSafetyScore": 0.95,
            "fraudRate": 0.02,
        },
        "VERIZON_MEDIA": {
            "id": 2,
            "name": "Verizon Media",
            "type": "owned",
            "description": "Verizon Media properties (AOL, HuffPost, TechCrunch, Engadget)",
            "avgCpm": 7.00,
            "viewabilityRate": 0.70,
            "dailyImpressions": 200000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "NATIVE"],
            "geoAvailability": ["US", "CA", "UK"],
            "brandSafetyScore": 0.92,
            "fraudRate": 0.03,
        },
        "MAGNITE": {
            "id": 3,
            "name": "Magnite (Rubicon)",
            "type": "ssp",
            "description": "Premium publisher inventory via Magnite SSP",
            "avgCpm": 8.50,
            "viewabilityRate": 0.68,
            "dailyImpressions": 800000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "AUDIO", "CTV"],
            "geoAvailability": ["GLOBAL"],
            "brandSafetyScore": 0.88,
            "fraudRate": 0.05,
            "premiumPublishers": ["ESPN", "CNN", "NYT", "WSJ", "NBC"],
        },
        "PUBMATIC": {
            "id": 4,
            "name": "PubMatic",
            "type": "ssp",
            "description": "PubMatic exchange - global programmatic marketplace",
            "avgCpm": 5.50,
            "viewabilityRate": 0.65,
            "dailyImpressions": 1200000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "NATIVE", "CTV"],
            "geoAvailability": ["GLOBAL"],
            "brandSafetyScore": 0.85,
            "fraudRate": 0.06,
        },
        "INDEX_EXCHANGE": {
            "id": 5,
            "name": "Index Exchange",
            "type": "ssp",
            "description": "Index Exchange - header bidding focused SSP",
            "avgCpm": 7.50,
            "viewabilityRate": 0.71,
            "dailyImpressions": 600000000,
            "mediaTypes": ["DISPLAY", "VIDEO"],
            "geoAvailability": ["US", "CA", "UK", "EU"],
            "brandSafetyScore": 0.90,
            "fraudRate": 0.04,
            "headerBiddingEnabled": True,
        },
        "OPENX": {
            "id": 6,
            "name": "OpenX",
            "type": "ssp",
            "description": "OpenX - premium programmatic marketplace",
            "avgCpm": 6.00,
            "viewabilityRate": 0.67,
            "dailyImpressions": 400000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "CTV"],
            "geoAvailability": ["GLOBAL"],
            "brandSafetyScore": 0.87,
            "fraudRate": 0.05,
        },
        "TRIPLELIFT": {
            "id": 7,
            "name": "TripleLift",
            "type": "ssp",
            "description": "TripleLift - native advertising exchange",
            "avgCpm": 9.00,
            "viewabilityRate": 0.75,
            "dailyImpressions": 150000000,
            "mediaTypes": ["NATIVE", "DISPLAY", "VIDEO"],
            "geoAvailability": ["US", "CA", "UK", "EU"],
            "brandSafetyScore": 0.91,
            "fraudRate": 0.03,
            "nativeFormats": ["in-feed", "in-article", "recommendation"],
        },
        "SHARETHROUGH": {
            "id": 8,
            "name": "Sharethrough",
            "type": "ssp",
            "description": "Sharethrough - native and video exchange",
            "avgCpm": 8.00,
            "viewabilityRate": 0.73,
            "dailyImpressions": 100000000,
            "mediaTypes": ["NATIVE", "VIDEO"],
            "geoAvailability": ["US", "CA"],
            "brandSafetyScore": 0.89,
            "fraudRate": 0.04,
        },
        "OPEN_EXCHANGE": {
            "id": 99,
            "name": "Open RTB Marketplace",
            "type": "open",
            "description": "Open marketplace - aggregated inventory from multiple sources",
            "avgCpm": 4.00,
            "viewabilityRate": 0.55,
            "dailyImpressions": 5000000000,
            "mediaTypes": ["DISPLAY", "VIDEO", "NATIVE", "AUDIO"],
            "geoAvailability": ["GLOBAL"],
            "brandSafetyScore": 0.70,
            "fraudRate": 0.12,
            "note": "Requires brand safety and fraud filtering",
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
    # https://help.yahooinc.com/dsp-api/docs/lines
    # =========================================================================
    FREQUENCY_CAP_TYPES = {
        "IMPRESSION": "Limit number of impressions per user",
        "CLICK": "Limit number of clicks per user",
    }
    
    FREQUENCY_CAP_DURATION_UNITS = {
        "HOUR": {"seconds": 3600, "description": "Per hour"},
        "DAY": {"seconds": 86400, "description": "Per day (24 hours)"},
        "WEEK": {"seconds": 604800, "description": "Per week (7 days)"},
        "MONTH": {"seconds": 2592000, "description": "Per month (30 days)"},
        "LIFETIME": {"seconds": None, "description": "Campaign lifetime"},
    }
    
    FREQUENCY_CAP_SCOPES = {
        "LINE": "Frequency cap applies to this Line only",
        "CAMPAIGN": "Frequency cap applies across all Lines in Campaign",
        "ADVERTISER": "Frequency cap applies across all Campaigns for Advertiser",
    }
    
    # Recommended frequency cap presets by goal type
    FREQUENCY_CAP_PRESETS = {
        "awareness": {"limit": 5, "duration": 1, "durationUnit": "DAY", "scope": "CAMPAIGN"},
        "consideration": {"limit": 3, "duration": 1, "durationUnit": "DAY", "scope": "LINE"},
        "conversion": {"limit": 7, "duration": 1, "durationUnit": "WEEK", "scope": "LINE"},
        "retargeting": {"limit": 10, "duration": 1, "durationUnit": "DAY", "scope": "ADVERTISER"},
    }

    # =========================================================================
    # Yahoo DSP Reporting Dimensions and Metrics
    # https://help.yahooinc.com/dsp-api/docs/reporting-api
    # =========================================================================
    REPORTING_DIMENSIONS = {
        "time": ["date", "hour", "week", "month"],
        "entity": ["advertiser", "campaign", "line", "ad", "creative"],
        "targeting": ["exchange", "deal", "device", "geo", "audience"],
        "delivery": ["domain", "app", "placement"],
    }
    
    REPORTING_METRICS = {
        # Volume metrics
        "impressions": {"type": "count", "description": "Total impressions served"},
        "clicks": {"type": "count", "description": "Total clicks"},
        "conversions": {"type": "count", "description": "Total conversions"},
        "videoCompletions": {"type": "count", "description": "Video completions (100%)"},
        "videoStarts": {"type": "count", "description": "Video starts"},
        "video25": {"type": "count", "description": "Video 25% completion"},
        "video50": {"type": "count", "description": "Video 50% completion"},
        "video75": {"type": "count", "description": "Video 75% completion"},
        
        # Cost metrics
        "spend": {"type": "currency", "description": "Total spend"},
        "mediaCost": {"type": "currency", "description": "Media cost (excluding fees)"},
        "dataFees": {"type": "currency", "description": "Third-party data fees"},
        
        # Rate metrics
        "cpm": {"type": "rate", "description": "Cost per 1000 impressions"},
        "cpc": {"type": "rate", "description": "Cost per click"},
        "cpa": {"type": "rate", "description": "Cost per acquisition"},
        "ctr": {"type": "percentage", "description": "Click-through rate"},
        "conversionRate": {"type": "percentage", "description": "Conversion rate"},
        "videoCompletionRate": {"type": "percentage", "description": "Video completion rate"},
        
        # Quality metrics
        "viewableImpressions": {"type": "count", "description": "Viewable impressions (MRC standard)"},
        "viewabilityRate": {"type": "percentage", "description": "Viewability rate"},
        "measurableImpressions": {"type": "count", "description": "Measurable impressions"},
        "measurabilityRate": {"type": "percentage", "description": "Measurability rate"},
        
        # Auction metrics
        "bidRequests": {"type": "count", "description": "Total bid requests received"},
        "bidsSubmitted": {"type": "count", "description": "Bids submitted to auction"},
        "bidsWon": {"type": "count", "description": "Auctions won"},
        "winRate": {"type": "percentage", "description": "Auction win rate"},
        "avgBid": {"type": "currency", "description": "Average bid amount"},
        "avgWinPrice": {"type": "currency", "description": "Average winning price"},
        
        # Reach metrics
        "uniqueUsers": {"type": "count", "description": "Unique users reached"},
        "frequency": {"type": "rate", "description": "Average frequency per user"},
    }

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
        pacing: str = "EVEN",
        campaign_days: int = 30,
        custom_targets: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Configure DSP bidding strategy (Yahoo DSP API style).
        
        Yahoo DSP bidding fields:
        - bidStrategy: AUTOBID or MAXBID
        - bidType: DYNAMIC or FIXED
        - goalType: IMPRESSION, CLICK, CONVERSION, etc.
        - maxBid: Maximum CPM bid
        - pacingType: EVEN or ACCELERATED
        - Learning phase and target metrics based on goal type
        
        Args:
            strategy: AUTOBID or MAXBID
            goal_type: IMPRESSION, CLICK, CONVERSION, VIEWABLE_IMPRESSION, VIDEO_COMPLETION
            max_bid: Maximum CPM bid amount
            total_budget: Total campaign budget
            pacing: EVEN or ACCELERATED
            campaign_days: Campaign duration in days (for target calculations)
            custom_targets: Override default target metrics
        """
        # Get strategy and goal configuration
        strategy_config = self.BID_STRATEGIES.get(strategy, self.BID_STRATEGIES["AUTOBID"])
        goal_config = self.GOAL_TYPES.get(goal_type, self.GOAL_TYPES["IMPRESSION"])
        pacing_config = self.PACING_TYPES.get(pacing, self.PACING_TYPES["EVEN"])
        
        config = {
            "bidStrategy": strategy,
            "bidType": strategy_config.get("bidType", "DYNAMIC") if isinstance(strategy_config, dict) else "DYNAMIC",
            "goalType": goal_type,
            "maxBid": max_bid,
            "pacingType": pacing,
            "budgetAllocation": "DAILY_CAP",
            
            # Learning phase configuration
            "learningPhase": {
                "enabled": strategy == "AUTOBID" and goal_config.get("learningPhaseDays", 0) > 0,
                "durationDays": goal_config.get("learningPhaseDays", 0),
                "minDataPoints": goal_config.get("minDataPoints", 0),
                "status": "NOT_STARTED",  # NOT_STARTED, IN_PROGRESS, COMPLETED, FAILED
            },
            
            # Pacing details
            "pacingDetails": {
                "algorithm": pacing_config.get("algorithm", "time_weighted") if isinstance(pacing_config, dict) else "time_weighted",
                "dailyBudget": round(total_budget / max(1, campaign_days), 2),
                "overspendAllowed": pacing_config.get("overspendAllowed", False) if isinstance(pacing_config, dict) else False,
            },
        }

        # Add goal-specific target configuration
        target_field = goal_config.get("targetField") if isinstance(goal_config, dict) else None
        if target_field:
            # Use custom target if provided, otherwise use default
            default_target = goal_config.get("defaultTarget")
            if custom_targets and target_field in custom_targets:
                config[target_field] = custom_targets[target_field]
            elif default_target is not None:
                config[target_field] = default_target
            elif goal_type == "CONVERSION":
                # Calculate target CPA based on budget and expected conversions
                expected_conversions = max(1, int(total_budget / 50))  # Assume $50 CPA
                config["targetCpa"] = round(total_budget / expected_conversions, 2)
        
        # Add bid adjustments for AUTOBID strategy
        if strategy == "AUTOBID":
            config["bidAdjustments"] = {
                "enabled": True,
                "maxAdjustment": 0.50,  # +/- 50% from base bid
                "factors": {
                    "deviceType": {"mobile": 1.1, "desktop": 1.0, "tablet": 0.9, "ctv": 1.2},
                    "dayOfWeek": {"weekday": 1.0, "weekend": 0.95},
                    "timeOfDay": {"morning": 0.9, "afternoon": 1.0, "evening": 1.15, "night": 0.8},
                    "exchange": {},  # Populated based on exchange performance
                },
            }
        
        # Add conversion tracking config if goal is CONVERSION
        if goal_type == "CONVERSION":
            config["conversionTracking"] = {
                "pixelRequired": goal_config.get("requiresPixel", True) if isinstance(goal_config, dict) else True,
                "attributionWindow": {
                    "clickThrough": 30,  # days
                    "viewThrough": 1,    # days
                },
                "deduplication": "FIRST_CLICK",  # FIRST_CLICK, LAST_CLICK, LINEAR
            }

        return config

    def _build_frequency_cap(
        self,
        limit: int = 3,
        duration: int = 1,
        duration_unit: str = "DAY",
        scope: str = "LINE",
        cap_type: str = "IMPRESSION",
        preset: str | None = None,
    ) -> dict[str, Any]:
        """
        Build frequency cap configuration (Yahoo DSP style).
        
        Yahoo DSP frequency cap structure:
        - type: IMPRESSION or CLICK
        - limit: Max impressions/clicks per user
        - duration: Time period value
        - durationUnit: HOUR, DAY, WEEK, MONTH, LIFETIME
        - scope: LINE, CAMPAIGN, ADVERTISER
        
        Args:
            limit: Maximum number of impressions/clicks per user
            duration: Time period (e.g., 1 for "1 DAY")
            duration_unit: HOUR, DAY, WEEK, MONTH, LIFETIME
            scope: LINE, CAMPAIGN, or ADVERTISER
            cap_type: IMPRESSION or CLICK
            preset: Optional preset name (awareness, consideration, conversion, retargeting)
        
        Returns:
            Frequency cap configuration dict
        """
        # Use preset if provided
        if preset and preset in self.FREQUENCY_CAP_PRESETS:
            preset_config = self.FREQUENCY_CAP_PRESETS[preset]
            limit = preset_config["limit"]
            duration = preset_config["duration"]
            duration_unit = preset_config["durationUnit"]
            scope = preset_config["scope"]
        
        # Validate duration unit
        if duration_unit not in self.FREQUENCY_CAP_DURATION_UNITS:
            duration_unit = "DAY"
        
        # Validate scope
        if scope not in self.FREQUENCY_CAP_SCOPES:
            scope = "LINE"
        
        # Validate cap type
        if cap_type not in self.FREQUENCY_CAP_TYPES:
            cap_type = "IMPRESSION"
        
        # Calculate effective cap period in seconds (for reporting)
        duration_info = self.FREQUENCY_CAP_DURATION_UNITS.get(duration_unit, {})
        seconds_per_unit = duration_info.get("seconds") if isinstance(duration_info, dict) else None
        effective_seconds = seconds_per_unit * duration if seconds_per_unit else None
        
        return {
            "type": cap_type,
            "limit": limit,
            "duration": duration,
            "durationUnit": duration_unit,
            "scope": scope,
            "effectivePeriodSeconds": effective_seconds,
            "description": f"Max {limit} {cap_type.lower()}s per user per {duration} {duration_unit.lower()}(s) at {scope.lower()} level",
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

    def _generate_exchange_breakdown(
        self,
        total_impressions: int,
        exchanges: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        Generate detailed exchange-level performance breakdown.
        
        Uses exchange metadata to simulate realistic performance differences
        between exchanges (viewability, CPM, fraud rate, etc.).
        """
        breakdown = {}
        remaining_impressions = total_impressions
        
        for i, exchange_key in enumerate(exchanges):
            exchange_info = self.EXCHANGES.get(exchange_key, {})
            
            # Distribute impressions (weighted by exchange size)
            if i == len(exchanges) - 1:
                exchange_impressions = remaining_impressions
            else:
                # Larger exchanges get more share
                daily_supply = exchange_info.get("dailyImpressions", 100000000)
                weight = min(0.5, daily_supply / 1000000000)  # Cap at 50%
                exchange_impressions = int(total_impressions * weight * random.uniform(0.8, 1.2))
                exchange_impressions = min(exchange_impressions, remaining_impressions)
                remaining_impressions -= exchange_impressions
            
            if exchange_impressions <= 0:
                continue
            
            # Use exchange metadata for realistic metrics
            base_viewability = exchange_info.get("viewabilityRate", 0.65)
            base_cpm = exchange_info.get("avgCpm", 5.00)
            fraud_rate = exchange_info.get("fraudRate", 0.05)
            brand_safety = exchange_info.get("brandSafetyScore", 0.85)
            
            # Add some variance
            viewability = base_viewability * random.uniform(0.95, 1.05)
            cpm = base_cpm * random.uniform(0.90, 1.10)
            
            # Calculate derived metrics
            clicks = int(exchange_impressions * random.uniform(0.0008, 0.0015))
            viewable_impressions = int(exchange_impressions * viewability)
            valid_impressions = int(exchange_impressions * (1 - fraud_rate))
            
            breakdown[exchange_key] = {
                "exchangeId": exchange_info.get("id", 0),
                "exchangeName": exchange_info.get("name", exchange_key),
                "exchangeType": exchange_info.get("type", "unknown"),
                "impressions": exchange_impressions,
                "viewableImpressions": viewable_impressions,
                "viewabilityRate": round(viewability, 3),
                "clicks": clicks,
                "ctr": round(clicks / exchange_impressions if exchange_impressions > 0 else 0, 5),
                "avgCpm": round(cpm, 2),
                "spend": round((exchange_impressions / 1000) * cpm, 2),
                "fraudRate": round(fraud_rate, 3),
                "validImpressions": valid_impressions,
                "brandSafetyScore": round(brand_safety, 2),
            }
        
        return breakdown

    def _generate_device_breakdown(self, total_impressions: int) -> dict[str, dict[str, Any]]:
        """Generate device-level performance breakdown."""
        # Typical device distribution
        device_shares = {
            "mobile": 0.55,
            "desktop": 0.30,
            "tablet": 0.08,
            "ctv": 0.05,
            "other": 0.02,
        }
        
        breakdown = {}
        for device, share in device_shares.items():
            impressions = int(total_impressions * share * random.uniform(0.9, 1.1))
            clicks = int(impressions * random.uniform(0.0008, 0.0018))
            
            breakdown[device] = {
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(clicks / impressions if impressions > 0 else 0, 5),
                "share": round(impressions / total_impressions if total_impressions > 0 else 0, 3),
            }
        
        return breakdown

    def _generate_video_metrics(self, impressions: int) -> dict[str, Any]:
        """Generate video-specific metrics for VIDEO media type."""
        video_starts = int(impressions * random.uniform(0.85, 0.95))
        video_25 = int(video_starts * random.uniform(0.80, 0.90))
        video_50 = int(video_25 * random.uniform(0.75, 0.85))
        video_75 = int(video_50 * random.uniform(0.70, 0.80))
        video_completions = int(video_75 * random.uniform(0.65, 0.80))
        
        return {
            "videoStarts": video_starts,
            "video25": video_25,
            "video50": video_50,
            "video75": video_75,
            "videoCompletions": video_completions,
            "videoCompletionRate": round(video_completions / video_starts if video_starts > 0 else 0, 3),
            "avgViewTime": round(random.uniform(15, 25), 1),  # seconds
            "avgPercentViewed": round(random.uniform(0.55, 0.75), 3),
        }

    def get_media_buy_delivery(
        self,
        media_buy_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        reporting_period: ReportingPeriod | None = None,
    ) -> AdapterGetMediaBuyDeliveryResponse:
        """
        Get DSP campaign performance with programmatic-specific metrics.
        
        Yahoo DSP Reporting API metrics (aligned with actual API):
        - impressions, clicks, conversions, spend
        - ctr, cpm, cpc, cpa
        - viewableImpressions, viewabilityRate, measurableImpressions
        - winRate, bidRequests, bidsWon, avgBid, avgWinPrice
        - videoStarts, video25, video50, video75, videoCompletions
        - uniqueUsers, frequency
        
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

            # Generate detailed breakdowns
            exchange_breakdown = self._generate_exchange_breakdown(
                impressions, 
                line.get("exchanges", self.default_exchanges)
            )
            device_breakdown = self._generate_device_breakdown(impressions)
            
            # Generate video metrics if VIDEO media type
            video_metrics = {}
            if line["mediaType"] == "VIDEO":
                video_metrics = self._generate_video_metrics(impressions)
            
            # Calculate reach metrics
            unique_users = int(impressions / random.uniform(2.5, 4.0))  # Avg frequency 2.5-4
            frequency = round(impressions / unique_users if unique_users > 0 else 0, 2)
            
            # Measurability (not all impressions can be measured for viewability)
            measurable_impressions = int(impressions * random.uniform(0.85, 0.95))
            measurability_rate = round(measurable_impressions / impressions if impressions > 0 else 0, 3)
            
            # Build comprehensive metadata
            metadata = {
                # Yahoo DSP Line info
                "lineId": line["id"],
                "lineName": line["name"],
                "lineStatus": status,
                "mediaType": line["mediaType"],
                "goalType": line.get("goalType", "IMPRESSION"),
                
                # Bidding metrics (Yahoo DSP Reporting API)
                "bidRequests": bid_requests,
                "bidsSubmitted": int(bid_requests * random.uniform(0.7, 0.9)),
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
                
                # Viewability metrics (MRC standard)
                "viewableImpressions": viewable_impressions,
                "viewabilityRate": round(viewability_rate, 3),
                "measurableImpressions": measurable_impressions,
                "measurabilityRate": measurability_rate,
                
                # Reach metrics
                "uniqueUsers": unique_users,
                "frequency": frequency,
                
                # Budget tracking
                "scheduleBudget": line["scheduleBudget"],
                "dailyBudget": line["dailyBudget"],
                "spend": round(spend, 2),
                "budgetUtilization": round(spend / budget if budget > 0 else 0, 3),
                "budgetRemaining": round(budget - spend, 2),
                
                # Cost breakdown
                "mediaCost": round(spend * 0.85, 2),  # 85% media cost
                "dataFees": round(spend * 0.10, 2),   # 10% data fees
                "platformFees": round(spend * 0.05, 2),  # 5% platform fees
                
                # Audience info
                "audienceSegments": len(line.get("audienceSegments", [])),
                
                # Detailed breakdowns (Yahoo DSP dimensions)
                "exchangeBreakdown": exchange_breakdown,
                "deviceBreakdown": device_breakdown,
            }
            
            # Add video metrics if applicable
            if video_metrics:
                metadata["videoMetrics"] = video_metrics
            
            # Add deal info if PMP
            if line.get("deal"):
                metadata["dealInfo"] = line["deal"]

            packages.append(
                PackagePerformance(
                    package_id=line["packageId"],
                    external_id=str(line["id"]),
                    status=pkg_status,
                    impressions=impressions,
                    clicks=clicks,
                    spend=round(spend, 2),
                    metadata=metadata,
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

    def associate_creatives(
        self,
        line_item_ids: list[str],
        platform_creative_ids: list[str],
    ) -> list[dict[str, Any]]:
        """
        Associate already-uploaded creatives with Lines.
        
        In Yahoo DSP, this creates Ad objects that link creatives to Lines.
        
        Args:
            line_item_ids: Yahoo DSP Line IDs
            platform_creative_ids: Yahoo DSP Creative IDs (already uploaded)
        
        Returns:
            List of association results with status for each combination
        """
        self.log(f"🔗 Yahoo DSP: Associating {len(platform_creative_ids)} creatives with {len(line_item_ids)} lines")
        
        results = []
        for line_id in line_item_ids:
            for creative_id in platform_creative_ids:
                # Create Ad object (association between Line and Creative)
                ad_id = random.randint(10000000, 99999999)
                
                results.append({
                    "line_item_id": line_id,
                    "creative_id": creative_id,
                    "ad_id": str(ad_id),
                    "status": "success",
                    "message": f"Created Ad {ad_id} linking Creative {creative_id} to Line {line_id}",
                })
                self.log(f"   ✓ Line {line_id} + Creative {creative_id} → Ad {ad_id}")
        
        return results

    def update_media_buy_performance_index(
        self,
        media_buy_id: str,
        package_performance: list[PackagePerformance],
    ) -> bool:
        """
        Update the performance index for packages in a media buy.
        
        Yahoo DSP uses this to adjust bid strategies based on performance.
        The performance index influences AUTOBID optimization.
        
        Args:
            media_buy_id: Yahoo DSP Campaign ID
            package_performance: List of package performance data
        
        Returns:
            True if update successful
        """
        campaign = self._campaigns.get(media_buy_id)
        if not campaign:
            self.log(f"⚠️ Campaign {media_buy_id} not found for performance index update")
            return False
        
        self.log(f"📈 Yahoo DSP: Updating performance index for {media_buy_id}")
        
        # Update bid adjustments based on performance
        for perf in package_performance:
            for line in campaign["lines"]:
                if line["packageId"] == perf.package_id:
                    # Calculate performance score
                    if perf.metadata:
                        ctr = perf.metadata.get("ctr", 0)
                        conversion_rate = perf.metadata.get("conversionRate", 0)
                        viewability = perf.metadata.get("viewabilityRate", 0)
                        
                        # Simple performance score (0-100)
                        perf_score = (
                            (ctr * 10000) * 0.3 +  # CTR weight
                            (conversion_rate * 100) * 0.4 +  # Conversion weight
                            (viewability * 100) * 0.3  # Viewability weight
                        )
                        
                        line["performanceScore"] = round(perf_score, 2)
                        line["lastPerformanceUpdate"] = datetime.now(UTC).isoformat()
                        
                        # Adjust bid based on performance
                        if perf_score > 70:
                            line["bidAdjustment"] = 1.15  # Increase bid 15%
                        elif perf_score > 50:
                            line["bidAdjustment"] = 1.0  # No change
                        else:
                            line["bidAdjustment"] = 0.90  # Decrease bid 10%
                        
                        self.log(f"   ✓ Line {line['id']}: Score={perf_score:.1f}, Bid Adj={line['bidAdjustment']:.2f}")
                    break
        
        return True
