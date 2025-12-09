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
    # CTV Publisher Deals Database (Pre-negotiated deals for Honda demo)
    # These represent deals negotiated between the agency and each CTV publisher,
    # now loaded into Yahoo DSP for programmatic execution.
    # =========================================================================
    CTV_DEALS_DATABASE: dict[str, dict[str, Any]] = {
        # Premium Streaming - Programmatic Guaranteed
        "DSE-HONDA-Q1-2026": {
            "deal_id": "DSE-HONDA-Q1-2026",
            "publisher": "Disney Streaming (DSE)",
            "publisher_id": "disney_streaming",
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 42.00,
            "guaranteed_impressions": 5000000,
            "min_spend": 210000,
            "inventory": ["Disney+", "Hulu", "ESPN+"],
            "content_categories": ["Entertainment", "Sports", "Family"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s", "60s"],
                "max_file_size_mb": 100,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "content_rating": True,
                "genre": True,
            },
            "brand_safety_tier": "PREMIUM",
            "viewability_guarantee": 0.85,
        },
        "PARA-HONDA-Q1-2026": {
            "deal_id": "PARA-HONDA-Q1-2026",
            "publisher": "Paramount",
            "publisher_id": "paramount",
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 38.00,
            "guaranteed_impressions": 4000000,
            "min_spend": 152000,
            "inventory": ["Paramount+", "Pluto TV", "CBS Sports"],
            "content_categories": ["Entertainment", "Sports", "News"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 75,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "content_rating": True,
                "genre": True,
            },
            "brand_safety_tier": "PREMIUM",
            "viewability_guarantee": 0.82,
        },
        "WBD-HONDA-Q1-2026": {
            "deal_id": "WBD-HONDA-Q1-2026",
            "publisher": "Warner Bros. Discovery",
            "publisher_id": "wbd",
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 40.00,
            "guaranteed_impressions": 4000000,
            "min_spend": 160000,
            "inventory": ["Max", "Discovery+", "CNN+", "TNT Sports"],
            "content_categories": ["Entertainment", "Sports", "News", "Documentary"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s", "60s"],
                "max_file_size_mb": 100,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "content_rating": True,
                "genre": True,
            },
            "brand_safety_tier": "PREMIUM",
            "viewability_guarantee": 0.83,
        },
        "HBO-HONDA-Q1-2026": {
            "deal_id": "HBO-HONDA-Q1-2026",
            "publisher": "HBO Max",
            "publisher_id": "hbo_max",
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 45.00,
            "guaranteed_impressions": 3000000,
            "min_spend": 135000,
            "inventory": ["HBO Max", "HBO Originals"],
            "content_categories": ["Premium Entertainment", "Drama", "Documentary"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 100,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "content_rating": True,
            },
            "brand_safety_tier": "ULTRA_PREMIUM",
            "viewability_guarantee": 0.90,
        },
        # AVOD / FAST - Private Marketplace (Auction-based)
        "TUBI-HONDA-Q1-2026": {
            "deal_id": "TUBI-HONDA-Q1-2026",
            "publisher": "Tubi",
            "publisher_id": "tubi",
            "deal_type": "PRIVATE_AUCTION",
            "media_type": "CTV_VIDEO",
            "floor_cpm": 22.00,
            "avg_win_cpm": 26.50,
            "available_impressions": 8000000,
            "estimated_win_rate": 0.65,
            "inventory": ["Tubi"],
            "content_categories": ["Movies", "TV Shows", "Sports"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "genre": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.75,
        },
        "FOX-HONDA-Q1-2026": {
            "deal_id": "FOX-HONDA-Q1-2026",
            "publisher": "Fox Sports",
            "publisher_id": "fox_sports",
            "deal_type": "PRIVATE_AUCTION",
            "media_type": "CTV_VIDEO",
            "floor_cpm": 35.00,
            "avg_win_cpm": 42.00,
            "available_impressions": 4000000,
            "estimated_win_rate": 0.55,
            "inventory": ["Fox Sports Live", "FS1", "FS2"],
            "content_categories": ["Sports", "Live Events"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 75,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "sport_type": True,
            },
            "brand_safety_tier": "PREMIUM",
            "viewability_guarantee": 0.80,
        },
        "ROKU-HONDA-Q1-2026": {
            "deal_id": "ROKU-HONDA-Q1-2026",
            "publisher": "Roku",
            "publisher_id": "roku",
            "deal_type": "PRIVATE_AUCTION",
            "media_type": "CTV_VIDEO",
            "floor_cpm": 28.00,
            "avg_win_cpm": 33.00,
            "available_impressions": 6000000,
            "estimated_win_rate": 0.60,
            "inventory": ["The Roku Channel", "Roku Originals"],
            "content_categories": ["Entertainment", "Movies", "Live TV"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "household": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.78,
            "special_features": ["ACR Data", "Household Targeting"],
        },
        "VEVO-HONDA-Q1-2026": {
            "deal_id": "VEVO-HONDA-Q1-2026",
            "publisher": "VEVO",
            "publisher_id": "vevo",
            "deal_type": "PRIVATE_AUCTION",
            "media_type": "CTV_VIDEO",
            "floor_cpm": 18.00,
            "avg_win_cpm": 22.00,
            "available_impressions": 5000000,
            "estimated_win_rate": 0.70,
            "inventory": ["VEVO Music Videos", "VEVO TV"],
            "content_categories": ["Music", "Entertainment"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "music_genre": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.72,
            "audience_skew": "18-34",
        },
        # OEM / Device Manufacturers - Preferred Deals
        "VIZIO-HONDA-Q1-2026": {
            "deal_id": "VIZIO-HONDA-Q1-2026",
            "publisher": "Vizio",
            "publisher_id": "vizio",
            "deal_type": "PREFERRED_DEAL",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 20.00,
            "available_impressions": 4000000,
            "inventory": ["WatchFree+", "Vizio Home Screen"],
            "content_categories": ["Entertainment", "Movies", "TV Shows"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "household": True,
                "acr_data": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.76,
            "special_features": ["ACR Data", "Native CTV Placement"],
        },
        "SAMG-HONDA-Q1-2026": {
            "deal_id": "SAMG-HONDA-Q1-2026",
            "publisher": "Samsung",
            "publisher_id": "samsung",
            "deal_type": "PREFERRED_DEAL",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 22.00,
            "available_impressions": 3000000,
            "inventory": ["Samsung TV+", "Samsung Home Screen"],
            "content_categories": ["Entertainment", "News", "Sports"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "household": True,
                "acr_data": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.74,
            "special_features": ["ACR Data", "First Screen Ads"],
        },
        "LG-HONDA-Q1-2026": {
            "deal_id": "LG-HONDA-Q1-2026",
            "publisher": "LG",
            "publisher_id": "lg",
            "deal_type": "PREFERRED_DEAL",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 20.00,
            "available_impressions": 2000000,
            "inventory": ["LG Channels", "LG Home Dashboard"],
            "content_categories": ["Entertainment", "News"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 50,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "household": True,
            },
            "brand_safety_tier": "STANDARD",
            "viewability_guarantee": 0.73,
        },
        "DISC-HONDA-Q1-2026": {
            "deal_id": "DISC-HONDA-Q1-2026",
            "publisher": "Discovery+",
            "publisher_id": "discovery_plus",
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "media_type": "CTV_VIDEO",
            "cpm_rate": 32.00,
            "guaranteed_impressions": 3000000,
            "min_spend": 96000,
            "inventory": ["Discovery+", "Food Network", "HGTV", "TLC"],
            "content_categories": ["Lifestyle", "Documentary", "Reality"],
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "status": "ACTIVE",
            "creative_specs": {
                "formats": ["15s", "30s"],
                "max_file_size_mb": 75,
                "aspect_ratios": ["16:9"],
                "audio_required": True,
            },
            "targeting_available": {
                "geo": True,
                "daypart": True,
                "device": True,
                "content_rating": True,
            },
            "brand_safety_tier": "PREMIUM",
            "viewability_guarantee": 0.80,
        },
    }

    # =========================================================================
    # Yahoo DSP Audience Segment Types (aligned with Yahoo DSP API)
    # https://help.yahooinc.com/dsp-api/docs/audiences
    # =========================================================================
    SEGMENT_TYPES = {
        "COMPOSITE": "Composite Audiences - Combined segment logic",
        "CONVERSIONRULE": "Conversion Rule Audience - Pixel-based retargeting",
        "CUSTOM": "Device ID Audiences - Custom device lists",
        "EMAIL": "Email/Phone Number Audiences - CRM match",
        "IPADDRESS": "IP Address Audiences - B2B targeting",
        "EVENTLEVEL": "Mail Event Audience - Email engagement",
        "FACT": "Third-party Fact data segments - Oracle, Experian, Polk",
        "GEORETARGET": "POI Audiences - Point of Interest visits",
        "INTEREST": "Yahoo Interest Category segments - Behavioral",
        "LOOKALIKE": "Lookalike Audience - Modeled from seed",
        "MRT": "Mail Domain Audiences - Email domain targeting",
        "SRT": "Search Keyword Audiences - Search behavior",
    }

    # Legacy alias for backward compatibility
    AUDIENCE_TYPES = {
        "FIRST_PARTY": "Advertiser's own data (CRM, site visitors)",
        "THIRD_PARTY": "Data provider segments (Oracle, Experian)",
        "YAHOO_OWNED": "Yahoo behavioral data",
        "LOOKALIKE": "Modeled audiences based on seed",
        "RETARGETING": "Site/app visitor retargeting",
    }

    # =========================================================================
    # Comprehensive Audience Segment Database (for getAudienceSegments API)
    # Organized by segment ID for efficient lookup
    # Includes automotive-focused segments for Honda demo
    # =========================================================================
    AUDIENCE_SEGMENT_DATABASE: dict[int, dict[str, Any]] = {
        # =====================================================================
        # INTEREST Segments (Yahoo Behavioral Data)
        # =====================================================================
        98765: {
            "id": 98765,
            "name": "Auto Intenders - SUV/Crossover",
            "segmentType": "INTEREST",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 8500000,
            "cpmLift": 0.15,
            "recency": "30_DAYS",
            "description": "Users actively researching SUVs and crossovers based on Yahoo search and content consumption",
            "keywords": ["auto", "SUV", "crossover", "vehicle", "car shopping", "honda", "toyota", "suv buyer"],
            "countryCodes": ["USA", "CAN"],
        },
        98770: {
            "id": 98770,
            "name": "Auto Enthusiasts - New Vehicle Research",
            "segmentType": "INTEREST",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 12000000,
            "cpmLift": 0.10,
            "recency": "45_DAYS",
            "description": "Users consuming automotive content and comparing vehicles",
            "keywords": ["auto", "car", "vehicle", "automotive", "new car", "car research"],
            "countryCodes": ["USA", "CAN", "GBR"],
        },
        98771: {
            "id": 98771,
            "name": "Family Vehicle Shoppers",
            "segmentType": "INTEREST",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 6200000,
            "cpmLift": 0.18,
            "recency": "30_DAYS",
            "description": "Users researching family-friendly vehicles, safety ratings, cargo space",
            "keywords": ["family car", "minivan", "safety", "car seats", "family SUV", "honda pilot", "cr-v"],
            "countryCodes": ["USA"],
        },
        98780: {
            "id": 98780,
            "name": "Outdoor Enthusiasts",
            "segmentType": "INTEREST",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 3500000,
            "cpmLift": 0.25,
            "recency": "30_DAYS",
            "description": "Users interested in outdoor activities, camping, hiking",
            "keywords": ["outdoor", "camping", "hiking", "adventure", "nature"],
            "countryCodes": ["USA", "CAN"],
        },
        98781: {
            "id": 98781,
            "name": "Eco-Conscious Consumers",
            "segmentType": "INTEREST",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 4200000,
            "cpmLift": 0.22,
            "recency": "30_DAYS",
            "description": "Users interested in sustainability, green products, eco-friendly lifestyle",
            "keywords": ["eco", "sustainable", "green", "environment", "hybrid", "electric vehicle"],
            "countryCodes": ["USA", "CAN", "GBR"],
        },
        
        # =====================================================================
        # FACT Segments (Third-Party Data Providers)
        # =====================================================================
        98766: {
            "id": 98766,
            "name": "Competitive Auto - Toyota/Subaru Considerers",
            "segmentType": "FACT",
            "status": "ACTIVE",
            "provider": "Oracle Data Cloud",
            "reach": 3200000,
            "cpmLift": 0.35,
            "dataFee": 1.50,
            "recency": "60_DAYS",
            "description": "Users who have shown purchase intent for Toyota RAV4, Subaru Outback, Forester",
            "keywords": ["toyota", "subaru", "rav4", "outback", "forester", "competitive", "auto intender"],
            "countryCodes": ["USA"],
        },
        98768: {
            "id": 98768,
            "name": "In-Market Auto - Near Purchase (90 days)",
            "segmentType": "FACT",
            "status": "ACTIVE",
            "provider": "Polk/IHS Markit",
            "reach": 2100000,
            "cpmLift": 0.65,
            "dataFee": 2.50,
            "recency": "30_DAYS",
            "description": "Users predicted to purchase a vehicle within 90 days based on registration and financial data",
            "keywords": ["in-market", "auto", "purchase", "near purchase", "vehicle buyer", "dealership"],
            "countryCodes": ["USA"],
        },
        98772: {
            "id": 98772,
            "name": "SUV/Crossover Intenders - Premium",
            "segmentType": "FACT",
            "status": "ACTIVE",
            "provider": "Experian",
            "reach": 4800000,
            "cpmLift": 0.45,
            "dataFee": 2.00,
            "recency": "45_DAYS",
            "description": "High-confidence SUV purchase intenders based on credit and lifestyle data",
            "keywords": ["SUV", "crossover", "premium", "auto intender", "vehicle purchase"],
            "countryCodes": ["USA", "CAN"],
        },
        98782: {
            "id": 98782,
            "name": "High Income Households ($100K+)",
            "segmentType": "FACT",
            "status": "ACTIVE",
            "provider": "Experian",
            "reach": 4200000,
            "cpmLift": 0.35,
            "dataFee": 1.75,
            "recency": "90_DAYS",
            "description": "Households with annual income over $100,000",
            "keywords": ["high income", "affluent", "premium", "luxury"],
            "countryCodes": ["USA"],
        },
        98783: {
            "id": 98783,
            "name": "Auto Service - Recent Maintenance",
            "segmentType": "FACT",
            "status": "ACTIVE",
            "provider": "Oracle Data Cloud",
            "reach": 5500000,
            "cpmLift": 0.20,
            "dataFee": 1.25,
            "recency": "30_DAYS",
            "description": "Vehicle owners who recently had maintenance or service performed",
            "keywords": ["auto service", "maintenance", "car repair", "oil change"],
            "countryCodes": ["USA"],
        },
        
        # =====================================================================
        # LOOKALIKE Segments (Modeled Audiences)
        # =====================================================================
        98767: {
            "id": 98767,
            "name": "Honda Website Converters - Lookalike",
            "segmentType": "LOOKALIKE",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 5100000,
            "cpmLift": 0.25,
            "recency": "FRESH",
            "seedAudience": "Honda.com build & price completers",
            "seedSize": 125000,
            "similarityScore": 0.85,
            "description": "Users similar to those who completed build & price on Honda.com",
            "keywords": ["honda", "lookalike", "converters", "build price"],
            "countryCodes": ["USA"],
        },
        98773: {
            "id": 98773,
            "name": "Honda Dealer Visitors - Lookalike",
            "segmentType": "LOOKALIKE",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 3800000,
            "cpmLift": 0.28,
            "recency": "FRESH",
            "seedAudience": "Honda dealer website visitors",
            "seedSize": 85000,
            "similarityScore": 0.82,
            "description": "Users similar to those who visited Honda dealer websites",
            "keywords": ["honda", "dealer", "lookalike", "dealership"],
            "countryCodes": ["USA"],
        },
        98784: {
            "id": 98784,
            "name": "SUV Buyers - Lookalike",
            "segmentType": "LOOKALIKE",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 6200000,
            "cpmLift": 0.30,
            "recency": "FRESH",
            "seedAudience": "Recent SUV purchasers (all brands)",
            "seedSize": 200000,
            "similarityScore": 0.78,
            "description": "Users similar to those who recently purchased an SUV",
            "keywords": ["SUV", "buyer", "lookalike", "purchase"],
            "countryCodes": ["USA", "CAN"],
        },
        
        # =====================================================================
        # CONVERSIONRULE Segments (Retargeting/Pixel-Based)
        # =====================================================================
        98774: {
            "id": 98774,
            "name": "Honda.com - CR-V Page Visitors",
            "segmentType": "CONVERSIONRULE",
            "status": "ACTIVE",
            "provider": "Honda",
            "reach": 450000,
            "cpmLift": 0.0,
            "recency": "30_DAYS",
            "description": "Users who visited CR-V pages on Honda.com in last 30 days",
            "keywords": ["honda", "cr-v", "retargeting", "website visitor"],
            "countryCodes": ["USA"],
            "pixelId": "honda_crv_pixel",
        },
        98775: {
            "id": 98775,
            "name": "Honda.com - Build & Price Abandoners",
            "segmentType": "CONVERSIONRULE",
            "status": "ACTIVE",
            "provider": "Honda",
            "reach": 180000,
            "cpmLift": 0.0,
            "recency": "14_DAYS",
            "description": "Users who started but didn't complete build & price",
            "keywords": ["honda", "abandoner", "build price", "retargeting"],
            "countryCodes": ["USA"],
            "pixelId": "honda_bp_abandon_pixel",
        },
        98785: {
            "id": 98785,
            "name": "Honda.com - All Site Visitors",
            "segmentType": "CONVERSIONRULE",
            "status": "ACTIVE",
            "provider": "Honda",
            "reach": 1200000,
            "cpmLift": 0.0,
            "recency": "30_DAYS",
            "description": "All Honda.com visitors in last 30 days",
            "keywords": ["honda", "retargeting", "website visitor", "site visitor"],
            "countryCodes": ["USA"],
            "pixelId": "honda_site_pixel",
        },
        98786: {
            "id": 98786,
            "name": "Honda.com - Dealer Locator Users",
            "segmentType": "CONVERSIONRULE",
            "status": "ACTIVE",
            "provider": "Honda",
            "reach": 320000,
            "cpmLift": 0.0,
            "recency": "14_DAYS",
            "description": "Users who used the dealer locator tool",
            "keywords": ["honda", "dealer locator", "retargeting", "high intent"],
            "countryCodes": ["USA"],
            "pixelId": "honda_dealer_locator_pixel",
        },
        
        # =====================================================================
        # SRT Segments (Search Keyword Audiences)
        # =====================================================================
        98790: {
            "id": 98790,
            "name": "SUV Search - Recent Queries",
            "segmentType": "SRT",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 2800000,
            "cpmLift": 0.40,
            "recency": "14_DAYS",
            "description": "Users who searched for SUV-related terms on Yahoo",
            "keywords": ["SUV", "search", "crossover search", "best SUV"],
            "countryCodes": ["USA"],
        },
        98791: {
            "id": 98791,
            "name": "Honda Search - Brand Queries",
            "segmentType": "SRT",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 1500000,
            "cpmLift": 0.50,
            "recency": "14_DAYS",
            "description": "Users who searched for Honda brand terms on Yahoo",
            "keywords": ["honda", "cr-v", "accord", "civic", "honda search"],
            "countryCodes": ["USA"],
        },
        
        # =====================================================================
        # GEORETARGET Segments (Point of Interest)
        # =====================================================================
        98795: {
            "id": 98795,
            "name": "Auto Dealership Visitors",
            "segmentType": "GEORETARGET",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 3500000,
            "cpmLift": 0.55,
            "recency": "30_DAYS",
            "description": "Users who visited auto dealerships in the past 30 days",
            "keywords": ["dealership", "geo", "auto dealer", "car lot"],
            "countryCodes": ["USA"],
        },
        98796: {
            "id": 98796,
            "name": "Honda Dealership Visitors",
            "segmentType": "GEORETARGET",
            "status": "ACTIVE",
            "provider": "Yahoo",
            "reach": 450000,
            "cpmLift": 0.60,
            "recency": "30_DAYS",
            "description": "Users who visited Honda dealerships specifically",
            "keywords": ["honda", "dealership", "geo", "honda dealer"],
            "countryCodes": ["USA"],
        },
    }

    # Legacy: Keep old format for backward compatibility with existing code
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

    # Class-level storage for campaigns and creatives (persists across adapter instances)
    # This is needed because each tool call creates a new adapter instance
    # In production, this would be stored in a database
    _campaigns_store: dict[str, dict] = {}
    _creatives_store: dict[str, dict] = {}

    def __init__(self, config, principal, dry_run=False, creative_engine=None, tenant_id=None):
        """Initialize Yahoo DSP adapter."""
        super().__init__(config, principal, dry_run, creative_engine, tenant_id)
        
        # Use class-level storage (shared across all instances)
        self._campaigns = YahooDSP._campaigns_store
        self._creatives = YahooDSP._creatives_store
        
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

    # =========================================================================
    # Yahoo DSP Audience Tools (getAudienceSegments, Get_analytics_for_audiences)
    # https://help.yahooinc.com/dsp-api/docs/audiences
    # =========================================================================

    def get_audience_segments(
        self,
        account_id: int | None = None,
        segment_type: str | None = None,
        status: str = "ACTIVE",
        keywords: str | None = None,
        query: str | None = None,
        country_codes: str | None = None,
        page: int = 1,
        limit: int = 50,
        include_iab_data_labels: bool = False,
    ) -> dict[str, Any]:
        """
        Query available audience segments (Yahoo DSP getAudienceSegments API).
        
        Aligned with Yahoo DSP Traffic API:
        https://help.yahooinc.com/dsp-api/docs/audiences
        
        Args:
            account_id: Advertiser ID (optional filter)
            segment_type: Filter by type (INTEREST, FACT, LOOKALIKE, CONVERSIONRULE, SRT, GEORETARGET)
            status: Segment status (ACTIVE, INACTIVE)
            keywords: Comma-separated search strings for name and description
            query: Search by name
            country_codes: Country ISO3 codes (comma-separated)
            page: Page number (1-indexed)
            limit: Results per page (max 100)
            include_iab_data_labels: Include IAB data labels in response
            
        Returns:
            Dict with segments list, pagination info, and total count
        """
        self.log(f"🔍 Yahoo DSP: Querying audience segments")
        self.log(f"   Filters: type={segment_type}, keywords={keywords}, status={status}")
        
        # Start with all segments from the database
        all_segments = list(self.AUDIENCE_SEGMENT_DATABASE.values())
        
        # Apply filters
        filtered_segments = []
        for segment in all_segments:
            # Filter by status
            if status and segment.get("status") != status:
                continue
            
            # Filter by segment type
            if segment_type and segment.get("segmentType") != segment_type:
                continue
            
            # Filter by country codes
            if country_codes:
                requested_countries = set(c.strip().upper() for c in country_codes.split(","))
                segment_countries = set(segment.get("countryCodes", []))
                if not requested_countries & segment_countries:
                    continue
            
            # Filter by keywords (search in name, description, and keywords field)
            if keywords:
                keyword_list = [k.strip().lower() for k in keywords.split(",")]
                segment_text = " ".join([
                    segment.get("name", "").lower(),
                    segment.get("description", "").lower(),
                    " ".join(segment.get("keywords", [])).lower(),
                ]).lower()
                
                # Check if any keyword matches
                if not any(kw in segment_text for kw in keyword_list):
                    continue
            
            # Filter by query (search in name only)
            if query:
                if query.lower() not in segment.get("name", "").lower():
                    continue
            
            filtered_segments.append(segment)
        
        # Sort by reach (descending)
        filtered_segments.sort(key=lambda s: s.get("reach", 0), reverse=True)
        
        # Pagination
        total_count = len(filtered_segments)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_segments = filtered_segments[start_idx:end_idx]
        
        # Build response in Yahoo DSP API format
        response_segments = []
        for seg in paginated_segments:
            response_seg = {
                "id": seg["id"],
                "name": seg["name"],
                "segmentType": seg["segmentType"],
                "status": seg.get("status", "ACTIVE"),
                "reach": seg.get("reach", 0),
                "description": seg.get("description", ""),
                "recency": seg.get("recency", "30_DAYS"),
                "cpmLift": seg.get("cpmLift", 0),
            }
            
            # Add provider info if available
            if "provider" in seg:
                response_seg["provider"] = seg["provider"]
            
            # Add data fee for FACT segments
            if seg["segmentType"] == "FACT" and "dataFee" in seg:
                response_seg["dataFee"] = seg["dataFee"]
            
            # Add lookalike-specific fields
            if seg["segmentType"] == "LOOKALIKE":
                if "seedAudience" in seg:
                    response_seg["seedAudience"] = seg["seedAudience"]
                if "seedSize" in seg:
                    response_seg["seedSize"] = seg["seedSize"]
                if "similarityScore" in seg:
                    response_seg["similarityScore"] = seg["similarityScore"]
            
            # Add pixel info for CONVERSIONRULE segments
            if seg["segmentType"] == "CONVERSIONRULE" and "pixelId" in seg:
                response_seg["pixelId"] = seg["pixelId"]
            
            response_segments.append(response_seg)
        
        self.log(f"   ✓ Found {total_count} segments, returning {len(response_segments)} (page {page})")
        
        return {
            "segments": response_segments,
            "totalCount": total_count,
            "page": page,
            "limit": limit,
            "hasMore": end_idx < total_count,
        }

    def get_segment_analytics(
        self,
        segment_ids: list[int],
    ) -> dict[str, Any]:
        """
        Get analytics for specific audience segments.
        
        Aligned with Yahoo DSP Get_analytics_for_audiences_segment API.
        
        Args:
            segment_ids: List of segment IDs to get analytics for
            
        Returns:
            Dict with segment analytics including reach, CPM, CTR, conversion rates, and overlap
        """
        self.log(f"📊 Yahoo DSP: Getting analytics for {len(segment_ids)} segments")
        
        analytics = []
        segment_data_for_overlap = {}  # For overlap calculation
        
        for seg_id in segment_ids:
            segment = self.AUDIENCE_SEGMENT_DATABASE.get(seg_id)
            if not segment:
                self.log(f"   ⚠️ Segment {seg_id} not found")
                continue
            
            segment_data_for_overlap[seg_id] = segment
            
            # Calculate simulated performance metrics based on segment type
            base_cpm = 6.50
            base_ctr = 0.0012
            base_conversion_rate = 0.020
            base_viewability = 0.70
            base_dealer_visit_rate = 0.004
            
            # Adjust metrics based on segment type
            segment_type = segment.get("segmentType", "INTEREST")
            
            if segment_type == "FACT":
                # Third-party data: higher CPM, higher conversion
                data_fee = segment.get("dataFee", 1.50)
                base_cpm += data_fee
                base_ctr *= 1.3
                base_conversion_rate *= 1.5
                base_dealer_visit_rate *= 1.8
            elif segment_type == "LOOKALIKE":
                # Lookalike: moderate lift
                base_ctr *= 1.5
                base_conversion_rate *= 1.6
                base_dealer_visit_rate *= 1.5
            elif segment_type == "CONVERSIONRULE":
                # Retargeting: highest conversion
                base_ctr *= 3.0
                base_conversion_rate *= 4.0
                base_dealer_visit_rate *= 2.5
            elif segment_type == "SRT":
                # Search: high intent
                base_ctr *= 2.0
                base_conversion_rate *= 2.5
                base_dealer_visit_rate *= 2.2
            elif segment_type == "GEORETARGET":
                # POI: strong physical intent
                base_ctr *= 1.8
                base_conversion_rate *= 2.0
                base_dealer_visit_rate *= 3.0
            
            # Apply CPM lift from segment data
            cpm_lift = segment.get("cpmLift", 0)
            effective_cpm = round(base_cpm * (1 + cpm_lift), 2)
            
            # Add variance
            ctr = round(base_ctr * random.uniform(0.85, 1.15), 5)
            conversion_rate = round(base_conversion_rate * random.uniform(0.85, 1.15), 4)
            viewability = round(base_viewability * random.uniform(0.95, 1.05), 3)
            dealer_visit_rate = round(base_dealer_visit_rate * random.uniform(0.85, 1.15), 5)
            
            # Build recommendation based on segment type
            if segment_type == "CONVERSIONRULE":
                recommendation = "RETARGETING - Highest conversion, limited scale"
            elif segment_type == "FACT" and "in-market" in segment.get("name", "").lower():
                recommendation = "CONVERSION - Highest intent, justify premium CPM"
            elif segment_type == "FACT" and "competitive" in segment.get("name", "").lower():
                recommendation = "CONQUEST - High intent, competitive shoppers"
            elif segment_type == "LOOKALIKE":
                recommendation = "CORE - High-quality lookalike, strong conversion"
            elif segment.get("reach", 0) > 5000000:
                recommendation = "SCALE - High reach, efficient CPM"
            else:
                recommendation = "CONSIDERATION - Good balance of reach and quality"
            
            # Calculate performance index (0-100)
            performance_index = min(100, int(
                (ctr * 10000) * 0.25 +
                (conversion_rate * 100) * 0.35 +
                (viewability * 100) * 0.20 +
                (dealer_visit_rate * 10000) * 0.20
            ))
            
            segment_analytics = {
                "segmentId": seg_id,
                "name": segment["name"],
                "segmentType": segment_type,
                "reach": segment.get("reach", 0),
                "avgCPM": effective_cpm,
                "historicalCTR": ctr,
                "viewabilityRate": viewability,
                "conversionRate": conversion_rate,
                "dealerVisitRate": dealer_visit_rate,
                "performanceIndex": performance_index,
                "recommendation": recommendation,
                "frequencyCapRecommendation": 4 if segment_type == "CONVERSIONRULE" else 3,
            }
            
            # Add provider info
            if "provider" in segment:
                segment_analytics["provider"] = segment["provider"]
            
            # Add data fee if applicable
            if segment_type == "FACT" and "dataFee" in segment:
                segment_analytics["dataFee"] = segment["dataFee"]
                segment_analytics["effectiveCPM"] = effective_cpm
            
            analytics.append(segment_analytics)
        
        # Calculate overlap between segments
        overlap_analysis = {}
        if len(segment_data_for_overlap) > 1:
            seg_ids = list(segment_data_for_overlap.keys())
            for i, seg_id1 in enumerate(seg_ids):
                overlap_analysis[seg_id1] = {}
                for seg_id2 in seg_ids[i+1:]:
                    # Simulate overlap based on keyword similarity
                    seg1_keywords = set(segment_data_for_overlap[seg_id1].get("keywords", []))
                    seg2_keywords = set(segment_data_for_overlap[seg_id2].get("keywords", []))
                    
                    if seg1_keywords and seg2_keywords:
                        keyword_overlap = len(seg1_keywords & seg2_keywords) / len(seg1_keywords | seg2_keywords)
                        overlap_pct = round(keyword_overlap * random.uniform(0.3, 0.5), 2)
                    else:
                        overlap_pct = round(random.uniform(0.15, 0.35), 2)
                    
                    overlap_analysis[seg_id1][seg_id2] = overlap_pct
                    if seg_id2 not in overlap_analysis:
                        overlap_analysis[seg_id2] = {}
                    overlap_analysis[seg_id2][seg_id1] = overlap_pct
        
        # Add overlap analysis to each segment's analytics
        for seg_analytics in analytics:
            seg_id = seg_analytics["segmentId"]
            if seg_id in overlap_analysis:
                seg_analytics["overlapAnalysis"] = overlap_analysis[seg_id]
        
        self.log(f"   ✓ Generated analytics for {len(analytics)} segments")
        
        return {
            "segmentAnalytics": analytics,
        }

    # =========================================================================
    # Yahoo DSP Deal Management Tools (/traffic/deals)
    # https://help.yahooinc.com/dsp-api/docs/traffic-api
    # =========================================================================

    def list_deals(
        self,
        advertiser_id: str | None = None,
        status: str = "ACTIVE",
        deal_type: list[str] | None = None,
        media_type: str | None = None,
        publisher: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List available PMP/PG deals for an advertiser.
        
        Aligned with Yahoo DSP Traffic API /traffic/deals endpoint.
        
        Args:
            advertiser_id: Advertiser ID (optional, for filtering deals by access)
            status: Deal status filter (ACTIVE, INACTIVE, EXPIRED)
            deal_type: Filter by deal types (PROGRAMMATIC_GUARANTEED, PRIVATE_AUCTION, PREFERRED_DEAL)
            media_type: Filter by media type (CTV_VIDEO, DISPLAY, AUDIO)
            publisher: Filter by publisher name (partial match)
            page: Page number (1-indexed)
            limit: Results per page (max 100)
            
        Returns:
            Dict with deals list, pagination, and summary statistics
        """
        self.log(f"🤝 Yahoo DSP: Listing available deals")
        self.log(f"   Filters: status={status}, deal_type={deal_type}, media_type={media_type}")
        
        # Start with all deals
        all_deals = list(self.CTV_DEALS_DATABASE.values())
        
        # Apply filters
        filtered_deals = []
        for deal in all_deals:
            # Filter by status
            if status and deal.get("status") != status:
                continue
            
            # Filter by deal type
            if deal_type:
                if deal.get("deal_type") not in deal_type:
                    continue
            
            # Filter by media type
            if media_type and deal.get("media_type") != media_type:
                continue
            
            # Filter by publisher (partial match)
            if publisher:
                if publisher.lower() not in deal.get("publisher", "").lower():
                    continue
            
            filtered_deals.append(deal)
        
        # Sort by CPM (highest first for PG, lowest floor for PMP)
        def sort_key(d):
            if d.get("deal_type") == "PROGRAMMATIC_GUARANTEED":
                return d.get("cpm_rate", 0)
            else:
                return d.get("floor_cpm", d.get("cpm_rate", 0))
        
        filtered_deals.sort(key=sort_key, reverse=True)
        
        # Pagination
        total_count = len(filtered_deals)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_deals = filtered_deals[start_idx:end_idx]
        
        # Calculate summary statistics
        total_impressions = 0
        total_budget_at_rate = 0
        pg_deals = 0
        pmp_deals = 0
        
        for deal in filtered_deals:
            if deal.get("deal_type") == "PROGRAMMATIC_GUARANTEED":
                imps = deal.get("guaranteed_impressions", 0)
                rate = deal.get("cpm_rate", 0)
                pg_deals += 1
            else:
                imps = deal.get("available_impressions", 0)
                rate = deal.get("floor_cpm", deal.get("cpm_rate", 0))
                pmp_deals += 1
            
            total_impressions += imps
            total_budget_at_rate += (imps / 1000) * rate
        
        # Build response
        response_deals = []
        for deal in paginated_deals:
            response_deal = {
                "deal_id": deal["deal_id"],
                "publisher": deal["publisher"],
                "deal_type": deal["deal_type"],
                "media_type": deal["media_type"],
                "inventory": deal.get("inventory", []),
                "content_categories": deal.get("content_categories", []),
                "start_date": deal.get("start_date"),
                "end_date": deal.get("end_date"),
                "status": deal.get("status"),
                "brand_safety_tier": deal.get("brand_safety_tier"),
                "viewability_guarantee": deal.get("viewability_guarantee"),
            }
            
            # Add pricing based on deal type
            if deal["deal_type"] == "PROGRAMMATIC_GUARANTEED":
                response_deal["cpm_rate"] = deal.get("cpm_rate")
                response_deal["guaranteed_impressions"] = deal.get("guaranteed_impressions")
                response_deal["min_spend"] = deal.get("min_spend")
            else:
                response_deal["floor_cpm"] = deal.get("floor_cpm")
                response_deal["avg_win_cpm"] = deal.get("avg_win_cpm")
                response_deal["available_impressions"] = deal.get("available_impressions")
                response_deal["estimated_win_rate"] = deal.get("estimated_win_rate")
                if deal["deal_type"] == "PREFERRED_DEAL":
                    response_deal["cpm_rate"] = deal.get("cpm_rate")
            
            response_deals.append(response_deal)
        
        self.log(f"   ✓ Found {total_count} deals ({pg_deals} PG, {pmp_deals} PMP)")
        self.log(f"   📊 Total available impressions: {total_impressions:,}")
        self.log(f"   💰 Total budget at rate: ${total_budget_at_rate:,.2f}")
        
        return {
            "deals": response_deals,
            "totalCount": total_count,
            "page": page,
            "limit": limit,
            "hasMore": end_idx < total_count,
            "summary": {
                "totalAvailableImpressions": total_impressions,
                "totalBudgetAtRate": round(total_budget_at_rate, 2),
                "pgDeals": pg_deals,
                "pmpDeals": pmp_deals,
            },
        }

    def get_deal_details(
        self,
        deal_id: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific deal.
        
        Aligned with Yahoo DSP Traffic API /traffic/deals/{dealId} endpoint.
        
        Args:
            deal_id: The deal ID to retrieve
            
        Returns:
            Dict with complete deal details including targeting options and creative specs
        """
        self.log(f"📋 Yahoo DSP: Getting details for deal {deal_id}")
        
        deal = self.CTV_DEALS_DATABASE.get(deal_id)
        if not deal:
            raise ValueError(f"Deal {deal_id} not found")
        
        # Build comprehensive response
        response = {
            "deal_id": deal["deal_id"],
            "publisher": deal["publisher"],
            "publisher_id": deal.get("publisher_id"),
            "deal_type": deal["deal_type"],
            "media_type": deal["media_type"],
            "status": deal.get("status"),
            
            # Inventory details
            "inventory": deal.get("inventory", []),
            "content_categories": deal.get("content_categories", []),
            
            # Flight dates
            "start_date": deal.get("start_date"),
            "end_date": deal.get("end_date"),
            
            # Quality metrics
            "brand_safety_tier": deal.get("brand_safety_tier"),
            "viewability_guarantee": deal.get("viewability_guarantee"),
            
            # Creative specifications
            "creative_specs": deal.get("creative_specs", {}),
            
            # Available targeting options
            "targeting_available": deal.get("targeting_available", {}),
            
            # Special features (if any)
            "special_features": deal.get("special_features", []),
        }
        
        # Add pricing based on deal type
        if deal["deal_type"] == "PROGRAMMATIC_GUARANTEED":
            response["pricing"] = {
                "type": "FIXED",
                "cpm_rate": deal.get("cpm_rate"),
                "guaranteed_impressions": deal.get("guaranteed_impressions"),
                "min_spend": deal.get("min_spend"),
                "currency": "USD",
            }
            # Calculate expected delivery
            response["forecast"] = {
                "guaranteed_impressions": deal.get("guaranteed_impressions"),
                "estimated_reach": int(deal.get("guaranteed_impressions", 0) / 3.5),
                "estimated_frequency": 3.5,
                "confidence": 0.95,
            }
        elif deal["deal_type"] == "PRIVATE_AUCTION":
            response["pricing"] = {
                "type": "AUCTION",
                "floor_cpm": deal.get("floor_cpm"),
                "avg_win_cpm": deal.get("avg_win_cpm"),
                "available_impressions": deal.get("available_impressions"),
                "estimated_win_rate": deal.get("estimated_win_rate"),
                "currency": "USD",
            }
            # Calculate expected delivery at suggested bid
            win_rate = deal.get("estimated_win_rate", 0.5)
            avail_imps = deal.get("available_impressions", 0)
            response["forecast"] = {
                "available_impressions": avail_imps,
                "estimated_wins_at_floor": int(avail_imps * win_rate),
                "recommended_bid": round(deal.get("avg_win_cpm", 0) * 1.05, 2),
                "estimated_reach": int(avail_imps * win_rate / 3.0),
                "confidence": 0.75,
            }
        else:  # PREFERRED_DEAL
            response["pricing"] = {
                "type": "FIXED_PRIORITY",
                "cpm_rate": deal.get("cpm_rate"),
                "available_impressions": deal.get("available_impressions"),
                "priority_access": True,
                "currency": "USD",
            }
            response["forecast"] = {
                "available_impressions": deal.get("available_impressions"),
                "estimated_reach": int(deal.get("available_impressions", 0) / 3.2),
                "confidence": 0.85,
            }
        
        # Add audience skew if available
        if "audience_skew" in deal:
            response["audience_insights"] = {
                "primary_demographic": deal["audience_skew"],
            }
        
        self.log(f"   ✓ Retrieved details for {deal['publisher']}")
        
        return response

    def create_dsp_campaign(
        self,
        advertiser_id: str,
        name: str,
        budget: float,
        currency: str = "USD",
        start_date: str = None,
        end_date: str = None,
        goal_type: str = "IMPRESSION",
        status: str = "INACTIVE",
    ) -> dict[str, Any]:
        """
        Create a new campaign (order) in Yahoo DSP.
        
        Aligned with Yahoo DSP Traffic API /traffic/campaigns endpoint.
        
        Args:
            advertiser_id: Advertiser ID
            name: Campaign name
            budget: Total campaign budget
            currency: Currency code (default USD)
            start_date: Campaign start date (YYYY-MM-DD)
            end_date: Campaign end date (YYYY-MM-DD)
            goal_type: Campaign goal (IMPRESSION, REACH, VIDEO_COMPLETION)
            status: Initial status (INACTIVE, ACTIVE)
            
        Returns:
            Dict with created campaign details including campaign_id
        """
        self.log(f"🎯 Yahoo DSP: Creating campaign '{name}'")
        
        # Generate campaign IDs
        campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
        order_id = random.randint(100000, 999999)
        
        # Parse dates
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=UTC)
        else:
            start_dt = datetime.now(UTC)
        
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=UTC)
        else:
            end_dt = start_dt + timedelta(days=30)
        
        campaign_days = max(1, (end_dt - start_dt).days)
        
        # Create campaign object
        campaign = {
            "campaign_id": campaign_id,
            "order_id": order_id,
            "advertiser_id": advertiser_id,
            "name": name,
            "budget": budget,
            "currency": currency,
            "daily_budget": round(budget / campaign_days, 2),
            "start_date": start_date or start_dt.strftime("%Y-%m-%d"),
            "end_date": end_date or end_dt.strftime("%Y-%m-%d"),
            "goal_type": goal_type,
            "status": status,
            "lines": [],
            "spend": 0,
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        # Store campaign
        self._campaigns[campaign_id] = campaign
        
        self.log(f"   ✅ Campaign created: {campaign_id}")
        self.log(f"   📋 Order ID: {order_id}")
        self.log(f"   💰 Budget: ${budget:,.2f}")
        
        return {
            "campaign_id": campaign_id,
            "order_id": order_id,
            "advertiser_id": advertiser_id,
            "name": name,
            "budget": budget,
            "daily_budget": campaign["daily_budget"],
            "currency": currency,
            "start_date": campaign["start_date"],
            "end_date": campaign["end_date"],
            "goal_type": goal_type,
            "status": status,
        }

    def create_line(
        self,
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
    ) -> dict[str, Any]:
        """
        Create a line item targeting specific deals.
        
        Aligned with Yahoo DSP Traffic API /traffic/lines endpoint.
        
        Args:
            campaign_id: Parent campaign ID
            name: Line name
            budget: Line budget
            deal_ids: List of deal IDs to target
            pacing: Pacing type (EVEN, ACCELERATED)
            bid_strategy: Bid strategy (AUTOBID, MAXBID)
            frequency_cap: Frequency cap configuration
            targeting: Additional targeting (geo, daypart, device)
            start_date: Line start date (optional, defaults to campaign dates)
            end_date: Line end date (optional, defaults to campaign dates)
            
        Returns:
            Dict with created line details including line_id and deal associations
        """
        self.log(f"📝 Yahoo DSP: Creating line '{name}' targeting {len(deal_ids)} deals")
        
        # Find campaign
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Generate line ID
        line_id = random.randint(1000000, 9999999)
        
        # Validate and collect deal info
        deals_info = []
        total_available_impressions = 0
        avg_cpm = 0
        
        for deal_id in deal_ids:
            deal = self.CTV_DEALS_DATABASE.get(deal_id)
            if not deal:
                self.log(f"   ⚠️ Deal {deal_id} not found, skipping")
                continue
            
            deals_info.append({
                "deal_id": deal_id,
                "publisher": deal["publisher"],
                "deal_type": deal["deal_type"],
                "cpm": deal.get("cpm_rate") or deal.get("floor_cpm", 0),
            })
            
            if deal["deal_type"] == "PROGRAMMATIC_GUARANTEED":
                total_available_impressions += deal.get("guaranteed_impressions", 0)
                avg_cpm += deal.get("cpm_rate", 0)
            else:
                total_available_impressions += deal.get("available_impressions", 0)
                avg_cpm += deal.get("floor_cpm", deal.get("cpm_rate", 0))
        
        if deals_info:
            avg_cpm = avg_cpm / len(deals_info)
        
        # Calculate campaign duration
        line_start = start_date or campaign.get("start_date")
        line_end = end_date or campaign.get("end_date")
        
        if line_start and line_end:
            start_dt = datetime.strptime(line_start, "%Y-%m-%d")
            end_dt = datetime.strptime(line_end, "%Y-%m-%d")
            campaign_days = max(1, (end_dt - start_dt).days)
        else:
            campaign_days = 90
        
        daily_budget = round(budget / campaign_days, 2)
        
        # Build frequency cap
        if frequency_cap:
            freq_cap = {
                "limit": frequency_cap.get("limit", 3),
                "duration": frequency_cap.get("duration", 7),
                "duration_unit": frequency_cap.get("unit", "DAY"),
                "scope": "LINE",
            }
        else:
            freq_cap = {
                "limit": 3,
                "duration": 7,
                "duration_unit": "DAY",
                "scope": "LINE",
            }
        
        # Create line object
        line = {
            "line_id": line_id,
            "campaign_id": campaign_id,
            "name": name,
            "budget": budget,
            "daily_budget": daily_budget,
            "deal_ids": deal_ids,
            "deals": deals_info,
            "pacing": pacing,
            "bid_strategy": bid_strategy,
            "max_bid": round(avg_cpm * 1.1, 2),  # 10% above average
            "frequency_cap": freq_cap,
            "targeting": targeting or {},
            "start_date": line_start,
            "end_date": line_end,
            "status": "PENDING_REVIEW",
            "media_type": "CTV_VIDEO",
            "creative_ids": [],
            "ad_ids": [],
            "spend": 0,
            "impressions": 0,
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        # Add to campaign
        campaign["lines"].append(line)
        
        # Estimate delivery
        estimated_impressions = min(
            int(budget / avg_cpm * 1000) if avg_cpm > 0 else 0,
            total_available_impressions
        )
        estimated_reach = int(estimated_impressions / 3.5)
        
        self.log(f"   ✅ Line created: {line_id}")
        self.log(f"   💰 Budget: ${budget:,.2f} (${daily_budget}/day)")
        self.log(f"   🎯 Targeting {len(deals_info)} deals")
        self.log(f"   📊 Est. impressions: {estimated_impressions:,}")
        
        return {
            "line_id": line_id,
            "campaign_id": campaign_id,
            "name": name,
            "budget": budget,
            "daily_budget": daily_budget,
            "deal_ids": deal_ids,
            "deals": deals_info,
            "pacing": pacing,
            "bid_strategy": bid_strategy,
            "max_bid": line["max_bid"],
            "frequency_cap": freq_cap,
            "targeting": targeting,
            "start_date": line_start,
            "end_date": line_end,
            "status": "PENDING_REVIEW",
            "media_type": "CTV_VIDEO",
            "estimated": {
                "impressions": estimated_impressions,
                "reach": estimated_reach,
                "avg_frequency": 3.5,
                "avg_cpm": round(avg_cpm, 2),
            },
        }

    def create_dsp_ad(
        self,
        line_id: int,
        creative_id: str,
        name: str,
        status: str = "ACTIVE",
    ) -> dict[str, Any]:
        """
        Associate a creative with a line item (create an Ad object).
        
        Aligned with Yahoo DSP Traffic API /traffic/ads endpoint.
        
        Args:
            line_id: Yahoo DSP Line ID
            creative_id: Creative ID to associate
            name: Ad name
            status: Initial status (ACTIVE, PAUSED)
            
        Returns:
            Dict with created ad details including ad_id
        """
        self.log(f"🎬 Yahoo DSP: Creating ad '{name}' for line {line_id}")
        
        # Generate ad ID
        ad_id = random.randint(10000000, 99999999)
        
        # Find the line and update it
        for campaign in self._campaigns.values():
            for line in campaign.get("lines", []):
                if line.get("line_id") == line_id:
                    if creative_id not in line.get("creative_ids", []):
                        line.setdefault("creative_ids", []).append(creative_id)
                    line.setdefault("ad_ids", []).append(ad_id)
                    break
        
        self.log(f"   ✅ Ad created: {ad_id}")
        
        return {
            "ad_id": ad_id,
            "line_id": line_id,
            "creative_id": creative_id,
            "name": name,
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def get_campaign_delivery(
        self,
        campaign_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        breakdown: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get delivery metrics for a campaign broken down by deal/line/creative.
        
        Aligned with Yahoo DSP Reporting API.
        
        Args:
            campaign_id: Campaign ID to get delivery for
            start_date: Report start date (YYYY-MM-DD)
            end_date: Report end date (YYYY-MM-DD)
            breakdown: Dimensions to break down by (deal, line, creative, device)
            
        Returns:
            Dict with delivery metrics and breakdowns
        """
        self.log(f"📊 Yahoo DSP: Getting delivery for campaign {campaign_id}")
        
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        breakdown = breakdown or ["deal", "line"]
        
        # Aggregate metrics
        total_impressions = 0
        total_clicks = 0
        total_spend = 0
        total_completions = 0
        
        line_metrics = []
        deal_metrics = {}
        
        for line in campaign.get("lines", []):
            # Simulate delivery based on budget
            budget = line.get("budget", 0)
            max_bid = line.get("max_bid", 30)
            
            # Calculate simulated metrics
            line_impressions = int(budget / max_bid * 1000 * random.uniform(0.7, 0.95))
            line_clicks = int(line_impressions * random.uniform(0.003, 0.008))  # 0.3-0.8% CTR for CTV
            line_spend = round(budget * random.uniform(0.6, 0.85), 2)
            line_completions = int(line_impressions * random.uniform(0.85, 0.95))  # Video completion
            
            total_impressions += line_impressions
            total_clicks += line_clicks
            total_spend += line_spend
            total_completions += line_completions
            
            # Per-deal breakdown
            deals = line.get("deals", [])
            impressions_per_deal = line_impressions // len(deals) if deals else line_impressions
            
            for deal_info in deals:
                deal_id = deal_info["deal_id"]
                deal_imps = int(impressions_per_deal * random.uniform(0.9, 1.1))
                deal_clicks = int(deal_imps * random.uniform(0.003, 0.008))
                deal_spend = round((deal_imps / 1000) * deal_info["cpm"], 2)
                deal_completions = int(deal_imps * random.uniform(0.85, 0.95))
                
                if deal_id not in deal_metrics:
                    deal_metrics[deal_id] = {
                        "deal_id": deal_id,
                        "publisher": deal_info["publisher"],
                        "deal_type": deal_info["deal_type"],
                        "impressions": 0,
                        "clicks": 0,
                        "spend": 0,
                        "video_completions": 0,
                    }
                
                deal_metrics[deal_id]["impressions"] += deal_imps
                deal_metrics[deal_id]["clicks"] += deal_clicks
                deal_metrics[deal_id]["spend"] += deal_spend
                deal_metrics[deal_id]["video_completions"] += deal_completions
            
            # Line metrics
            line_metrics.append({
                "line_id": line.get("line_id"),
                "name": line.get("name"),
                "budget": budget,
                "spend": line_spend,
                "pacing": round(line_spend / budget if budget > 0 else 0, 2),
                "impressions": line_impressions,
                "clicks": line_clicks,
                "video_completions": line_completions,
                "ctr": round(line_clicks / line_impressions if line_impressions > 0 else 0, 4),
                "vcr": round(line_completions / line_impressions if line_impressions > 0 else 0, 3),
                "cpm": round(line_spend / line_impressions * 1000 if line_impressions > 0 else 0, 2),
            })
        
        # Finalize deal metrics with rates
        for deal_id, metrics in deal_metrics.items():
            imps = metrics["impressions"]
            metrics["ctr"] = round(metrics["clicks"] / imps if imps > 0 else 0, 4)
            metrics["vcr"] = round(metrics["video_completions"] / imps if imps > 0 else 0, 3)
            metrics["cpm"] = round(metrics["spend"] / imps * 1000 if imps > 0 else 0, 2)
        
        self.log(f"   📈 Total impressions: {total_impressions:,}")
        self.log(f"   🎬 Video completions: {total_completions:,} ({round(total_completions/total_impressions*100 if total_impressions else 0, 1)}% VCR)")
        self.log(f"   💰 Total spend: ${total_spend:,.2f}")
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign.get("name"),
            "report_period": {
                "start_date": start_date or campaign.get("start_date"),
                "end_date": end_date or campaign.get("end_date"),
            },
            "totals": {
                "impressions": total_impressions,
                "clicks": total_clicks,
                "spend": round(total_spend, 2),
                "video_completions": total_completions,
                "ctr": round(total_clicks / total_impressions if total_impressions > 0 else 0, 4),
                "vcr": round(total_completions / total_impressions if total_impressions > 0 else 0, 3),
                "cpm": round(total_spend / total_impressions * 1000 if total_impressions > 0 else 0, 2),
                "budget": campaign.get("budget", 0),
                "pacing": round(total_spend / campaign.get("budget", 1) if campaign.get("budget") else 0, 2),
            },
            "by_line": line_metrics if "line" in breakdown else None,
            "by_deal": list(deal_metrics.values()) if "deal" in breakdown else None,
        }

    # =========================================================================
    # Agency Workflow Methods (Prisma Integration)
    # =========================================================================
    
    def register_deal(
        self,
        deal_id: str,
        publisher: str,
        impressions: int,
        cpm_rate: float,
        ssp: str = "FreeWheel",
        advertiser_id: str = "honda_motor_company",
        campaign_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Register a PG deal received from a publisher via email.
        
        This simulates the Yahoo DSP workflow where agencies:
        1. Negotiate deals directly with publishers
        2. Receive deal IDs via email
        3. Register deals in Yahoo DSP
        4. First deal creates campaign, subsequent deals add to it
        
        Args:
            deal_id: Deal ID from publisher
            publisher: Publisher name
            impressions: Guaranteed impressions
            cpm_rate: CPM rate in dollars
            ssp: Supply-side platform
            advertiser_id: Advertiser ID
            campaign_name: Campaign name (for first deal)
            
        Returns:
            Dict with registered deal, campaign, and line info
        """
        self.log(f"📝 Yahoo DSP: Registering deal {deal_id} from {publisher}")
        self.log(f"   📺 SSP: {ssp} | Imps: {impressions:,} | CPM: ${cpm_rate}")
        
        # Calculate deal value
        deal_value = round((impressions / 1000) * cpm_rate, 2)
        
        # Create deal entry
        deal = {
            "deal_id": deal_id,
            "publisher": publisher,
            "deal_type": "PROGRAMMATIC_GUARANTEED",
            "status": "ACTIVE",
            "media_type": "CTV_VIDEO",
            "ssp": ssp,
            "guaranteed_impressions": impressions,
            "cpm_rate": cpm_rate,
            "deal_value": deal_value,
            "apps": [f"{publisher} App", f"{publisher}+ Streaming"],
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        # Add to deals database
        self.CTV_DEALS_DATABASE[deal_id] = deal
        
        # Check for existing campaign or create new one
        campaign = None
        campaign_created = False
        
        # Find campaign for this advertiser
        for camp_id, camp in self._campaigns.items():
            if camp.get("advertiser_id") == advertiser_id:
                campaign = camp
                break
        
        if not campaign:
            # Create new campaign (first deal)
            campaign_created = True
            campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
            campaign_name = campaign_name or f"{advertiser_id.replace('_', ' ').title()} CTV Q1 2026"
            
            campaign = {
                "campaign_id": campaign_id,
                "advertiser_id": advertiser_id,
                "name": campaign_name,
                "budget": deal_value,  # Start with first deal value
                "daily_budget": round(deal_value / 90, 2),
                "currency": "USD",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "goal_type": "IMPRESSION",
                "status": "INACTIVE",
                "lines": [],
                "deals": [deal_id],
                "created_at": datetime.now(UTC).isoformat(),
            }
            self._campaigns[campaign_id] = campaign
            self.log(f"   🆕 Created new campaign: {campaign_name}")
        else:
            # Add to existing campaign
            campaign["budget"] = round(campaign.get("budget", 0) + deal_value, 2)
            campaign["daily_budget"] = round(campaign["budget"] / 90, 2)
            campaign.setdefault("deals", []).append(deal_id)
            campaign_id = campaign["campaign_id"]
            self.log(f"   ➕ Added to existing campaign: {campaign.get('name')}")
        
        # Create line for this deal
        line_id = random.randint(1000000, 9999999)
        line = {
            "line_id": line_id,
            "campaign_id": campaign_id,
            "name": f"{publisher} - PG",
            "budget": deal_value,
            "daily_budget": round(deal_value / 90, 2),
            "deal_ids": [deal_id],
            "deals": [{
                "deal_id": deal_id,
                "publisher": publisher,
                "deal_type": "PROGRAMMATIC_GUARANTEED",
                "cpm": cpm_rate,
            }],
            "pacing": "EVEN",
            "bid_strategy": "AUTOBID",
            "frequency_cap": {"limit": 3, "duration": 7, "duration_unit": "DAY"},
            "start_date": campaign["start_date"],
            "end_date": campaign["end_date"],
            "status": "PENDING_REVIEW",
            "media_type": "CTV_VIDEO",
            "creative_ids": [],
            "ad_ids": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
        campaign["lines"].append(line)
        
        # Count total deals and budget
        total_deals = len(campaign.get("deals", []))
        total_budget = campaign["budget"]
        
        self.log(f"   ✅ Deal registered successfully")
        self.log(f"   📊 Campaign total: {total_deals} deals, ${total_budget:,.2f} budget")
        
        return {
            "success": True,
            "deal": {
                "deal_id": deal_id,
                "publisher": publisher,
                "ssp": ssp,
                "impressions": impressions,
                "cpm_rate": cpm_rate,
                "deal_value": deal_value,
                "status": "ACTIVE",
            },
            "campaign": {
                "campaign_id": campaign_id,
                "name": campaign.get("name"),
                "is_new": campaign_created,
                "total_budget": total_budget,
                "total_deals": total_deals,
                "status": campaign["status"],
            },
            "line": {
                "line_id": line_id,
                "name": line["name"],
                "budget": deal_value,
                "deal_ids": [deal_id],
                "status": "PENDING_REVIEW",
            },
            "message": f"Deal {deal_id} from {publisher} registered. " + (
                f"Created new campaign '{campaign.get('name')}'" if campaign_created 
                else f"Added to campaign '{campaign.get('name')}' ({total_deals} deals, ${total_budget:,.2f})"
            ),
        }

    def register_innovid_tag(
        self,
        tag_url: str,
        name: str,
        duration: int = 30,
        width: int = 1920,
        height: int = 1080,
        line_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Register an Innovid VAST tag as a creative in Yahoo DSP.
        
        Innovid is a leading creative management platform for CTV.
        This simulates registering their VAST tag URLs as Yahoo DSP creatives.
        
        Args:
            tag_url: Innovid VAST tag URL
            name: Creative name
            duration: Video duration in seconds
            width: Video width
            height: Video height
            line_ids: Line IDs to assign this creative to
            
        Returns:
            Dict with registered creative and assignment info
        """
        self.log(f"🎬 Yahoo DSP: Registering Innovid tag '{name}'")
        self.log(f"   📺 Format: {width}x{height}, {duration}s")
        
        # Generate creative ID
        creative_id = f"crv_{uuid.uuid4().hex[:8]}"
        
        # Determine format
        if duration <= 15:
            format_id = "ctv_video_15s"
        elif duration <= 30:
            format_id = "ctv_video_30s"
        else:
            format_id = "ctv_video_60s"
        
        # Create creative record
        creative = {
            "creative_id": creative_id,
            "name": name,
            "type": "VAST_TAG",
            "tag_url": tag_url,
            "duration": duration,
            "width": width,
            "height": height,
            "format_id": format_id,
            "aspect_ratio": "16:9" if width/height > 1.5 else "4:3",
            "status": "ACTIVE",
            "assigned_lines": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        # Assign to lines if specified
        assigned_lines = []
        if line_ids:
            for campaign in self._campaigns.values():
                for line in campaign.get("lines", []):
                    if line.get("line_id") in line_ids:
                        if creative_id not in line.get("creative_ids", []):
                            line.setdefault("creative_ids", []).append(creative_id)
                        assigned_lines.append({
                            "line_id": line["line_id"],
                            "line_name": line["name"],
                        })
                        creative["assigned_lines"].append(line["line_id"])
        
        # Store creative
        self._creatives[creative_id] = creative
        
        self.log(f"   ✅ Creative registered: {creative_id}")
        if assigned_lines:
            self.log(f"   🔗 Assigned to {len(assigned_lines)} lines")
        
        return {
            "success": True,
            "creative_id": creative_id,
            "name": name,
            "type": "VAST_TAG",
            "format": {
                "format_id": format_id,
                "duration": duration,
                "width": width,
                "height": height,
                "aspect_ratio": creative["aspect_ratio"],
            },
            "tag_url": tag_url,
            "status": "ACTIVE",
            "assigned_lines": assigned_lines,
            "message": f"Innovid tag '{name}' registered as creative {creative_id}" + (
                f" and assigned to {len(assigned_lines)} lines" if assigned_lines else ""
            ),
        }

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
