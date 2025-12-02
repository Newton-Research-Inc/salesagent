# Newton + Yahoo DSP Demo Script

## 🎯 Demo Objective

Show Newton buying media through **Yahoo DSP (programmatic)** vs **ESPN (direct publisher)**, highlighting:
1. **Audience targeting** (DSP) vs placement targeting (publisher)
2. **Auction-based pricing** (DSP) vs fixed pricing (publisher)
3. **Rich performance metrics** (DSP) vs basic metrics (publisher)
4. **Strategic decision-making** by Newton based on audience analysis

---

## 📋 Demo Scenario

**Brand:** "Performance Outerwear Brand" (POB) - Premium outdoor apparel company (think Patagonia/Columbia)

**Campaign Goal:** Launch new sustainable hiking collection to eco-conscious outdoor enthusiasts with a $50K budget.

**Target Audience:** (Pre-identified through separate analysis)
- Outdoor enthusiasts (hiking, camping, trail running)
- Eco-conscious consumers who value sustainability
- Age 25-45, household income $75K+
- Active lifestyle, weekend adventurers

**Newton's Task:** 
- Evaluate where to find this specific audience
- Compare direct publisher (ESPN) vs programmatic DSP (Yahoo) capabilities
- Choose the strategy that best reaches the target audience
- Execute the buy and demonstrate ROI

---

## 🎬 Demo Script

### **Act 1: Discovery Phase - "Finding the Right Audience"**

Newton has been given a specific audience profile and needs to determine which platform can best reach them.

```python
# Newton's internal reasoning:
"I have a very specific target audience for Performance Outerwear Brand:
outdoor enthusiasts who value sustainability. This isn't a broad 
sports audience - it's a niche group. Let me query the available 
sales agents to see who can help me reach THIS specific audience."

# Tool calls:
mcp_espn.get_products(brief="outdoor enthusiasts, eco-conscious, sustainable products")
mcp_cnn.get_products(brief="outdoor enthusiasts, eco-conscious, sustainability")
mcp_yahoo.get_products(brief="outdoor enthusiasts, hiking, camping, eco-conscious consumers, sustainable products")
```

---

#### **ESPN Response (Placement-Based)**

```json
{
  "products": [
    {
      "product_id": "espn_display_728x90",
      "name": "ESPN Homepage Leaderboard",
      "description": "Premium placement on ESPN.com homepage",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 5.00,
        "currency": "USD",
        "is_fixed": true
      }],
      "properties": ["espn.com"],
      "inventory_profile": {
        "daily_available_impressions": 500000
      },
      "targeting_constraints": {
        "geo_targeting": ["US"],
        "device_types": ["desktop", "mobile"]
      }
    }
  ]
}
```

**Newton's Analysis:**
```
ESPN Analysis:
✅ Pros: Broad reach (500K daily), affordable CPM ($5.00)
❌ Cons: NO audience targeting - reaches ALL ESPN visitors
❌ Cons: Sports focus doesn't align with outdoor/sustainability
❌ Cons: Can only target by placement (homepage), not by audience

Audience Match: POOR
- ESPN = Sports fans (basketball, football, etc.)
- POB Target = Outdoor enthusiasts (hiking, camping)
- Overlap: ~5% (some sports fans do outdoor activities)

Reach Efficiency: LOW
- 500K daily impressions, but only ~25K are relevant
- Effective CPM: $100 (95% wasted impressions)
```

---

#### **CNN Response (Contextual Targeting)**

```json
{
  "products": [
    {
      "product_id": "cnn_display_300x250",
      "name": "CNN Climate Section - Medium Rectangle",
      "description": "Placement in CNN's Climate & Environment coverage",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 7.00,
        "currency": "USD",
        "is_fixed": true
      }],
      "properties": ["cnn.com/climate"],
      "inventory_profile": {
        "daily_available_impressions": 150000
      },
      "targeting_constraints": {
        "contextual": "Climate & environment news readers",
        "geo_targeting": ["US"]
      }
    }
  ]
}
```

**Newton's Analysis:**
```
CNN Analysis:
✅ Pros: Contextual alignment - Climate section attracts eco-conscious readers
✅ Pros: Better than ESPN - environmental content = relevant mindset
❌ Cons: Still placement-based, not audience-based
❌ Cons: Lower reach (150K daily) due to section-specific placement
❌ Cons: Higher CPM ($7.00) for lower volume

Audience Match: MEDIUM
- CNN Climate = Environmental news readers
- POB Target = Eco-conscious + outdoor active
- Overlap: ~20% (news readers ≠ outdoor gear buyers)

Reach Efficiency: MEDIUM
- 150K daily impressions, but only ~30K are relevant
- Effective CPM: $35 (80% waste - reading about climate ≠ buying hiking gear)
```

---

#### **Yahoo DSP Response (Audience-Based)**

> **Note:** Yahoo DSP products include rich metadata about exchanges, audience segments, 
> and bidding capabilities aligned with the Yahoo DSP API.

```json
{
  "products": [
    {
      "product_id": "yahoo_display_300x250",
      "name": "Audience-Targeted Display + Retargeting",
      "description": "Programmatic display with advanced audience targeting across Yahoo Exchange and open web. Supports outdoor_enthusiasts, eco_conscious_consumers, sustainable_shoppers audience segments. AUTOBID optimization available.",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 8.00,
        "currency": "USD",
        "is_fixed": false,
        "price_guidance": {
          "floor": 6.00,
          "p50": 8.00,
          "p75": 10.00
        }
      }],
      
      // Exchanges available (Yahoo DSP supply sources)
      "exchanges": [
        {
          "id": "YAHOO_EXCHANGE",
          "name": "Yahoo Exchange",
          "type": "owned",
          "avgCpm": 6.50,
          "viewabilityRate": 0.72,
          "brandSafetyScore": 0.95
        },
        {
          "id": "INDEX_EXCHANGE",
          "name": "Index Exchange",
          "type": "ssp",
          "avgCpm": 7.50,
          "viewabilityRate": 0.71,
          "brandSafetyScore": 0.90
        },
        {
          "id": "MAGNITE",
          "name": "Magnite (Rubicon)",
          "type": "ssp",
          "avgCpm": 8.50,
          "viewabilityRate": 0.68,
          "premiumPublishers": ["ESPN", "CNN", "NYT", "WSJ"]
        },
        {
          "id": "TRIPLELIFT",
          "name": "TripleLift",
          "type": "ssp",
          "avgCpm": 9.00,
          "viewabilityRate": 0.75,
          "nativeFormats": ["in-feed", "in-article"]
        },
        {
          "id": "OPEN_EXCHANGE",
          "name": "Open RTB Marketplace",
          "type": "open",
          "avgCpm": 4.00,
          "viewabilityRate": 0.55,
          "dailyImpressions": 5000000000
        }
      ],
      
      // Audience segments with provider metadata
      "targeting_capabilities": {
        "audience_segments": [
          {
            "id": "outdoor_enthusiasts",
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 3500000,
            "cpmLift": 0.25,
            "recency": "30_DAYS"
          },
          {
            "id": "eco_conscious_consumers",
            "type": "THIRD_PARTY",
            "provider": "Oracle Data Cloud",
            "reach": 2800000,
            "cpmLift": 0.30,
            "recency": "60_DAYS"
          },
          {
            "id": "adventure_travelers",
            "type": "YAHOO_OWNED",
            "provider": "Yahoo",
            "reach": 1900000,
            "cpmLift": 0.28,
            "recency": "45_DAYS"
          },
          {
            "id": "sustainable_shoppers",
            "type": "THIRD_PARTY",
            "provider": "Experian",
            "reach": 1500000,
            "cpmLift": 0.35,
            "recency": "30_DAYS"
          }
        ],
        "behavioral_targeting": true,
        "lookalike_audiences": true,
        "retargeting": true,
        "contextual_keywords": ["hiking", "camping", "outdoor gear", "sustainability", "eco-friendly"]
      },
      
      // Bidding capabilities (Yahoo DSP API)
      "bidding_capabilities": {
        "strategies": ["AUTOBID", "MAXBID"],
        "goalTypes": ["IMPRESSION", "CLICK", "CONVERSION", "VIEWABLE_IMPRESSION"],
        "pacingTypes": ["EVEN", "ACCELERATED"],
        "learningPhaseSupported": true
      },
      
      // Frequency cap presets
      "frequency_cap_presets": {
        "awareness": {"limit": 5, "duration": 1, "durationUnit": "DAY"},
        "consideration": {"limit": 3, "duration": 1, "durationUnit": "DAY"},
        "conversion": {"limit": 7, "duration": 1, "durationUnit": "WEEK"}
      },
      
      "performance_tracking": {
        "conversions": true,
        "viewability": true,
        "brand_lift": true,
        "audience_insights": true,
        "exchangeBreakdown": true,
        "deviceBreakdown": true
      }
    },
    {
      "product_id": "yahoo_display_300x250_pmp_sports",
      "name": "Premium PMP Deal - Sports & Outdoor Publishers",
      "description": "Private Marketplace (PMP) deal with premium sports and outdoor publishers. PREFERRED_DEAL type with fixed floor price. Higher viewability (75%+) and brand-safe inventory.",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 12.00,
        "currency": "USD",
        "is_fixed": false,
        "price_guidance": {
          "floor": 10.00,
          "p50": 12.00,
          "p75": 15.00
        }
      }],
      "deal_info": {
        "dealType": "PREFERRED_DEAL",
        "guaranteed": false,
        "publishers": ["Outside Magazine", "REI Co-op", "Backpacker", "Trail Runner"]
      }
    }
  ]
}
```

**Newton's Analysis:**
```
Yahoo DSP Analysis:
✅ Pros: AUDIENCE-FIRST targeting - can specifically target outdoor enthusiasts
✅ Pros: Multiple relevant segments available with provider metadata:
    - outdoor_enthusiasts (YAHOO_OWNED, 3.5M reach, 30-day recency) - EXACT match
    - eco_conscious_consumers (Oracle Data Cloud, 2.8M reach) - EXACT match
    - adventure_travelers (YAHOO_OWNED, 1.9M reach) - HIGH relevance
    - sustainable_shoppers (Experian, 1.5M reach) - HIGH relevance
✅ Pros: 9 exchanges available (Yahoo, Index, Magnite, TripleLift, etc.)
✅ Pros: Premium PMP deal option for sports/outdoor publishers ($12 CPM)
✅ Pros: AUTOBID optimization with learning phase support
✅ Pros: Retargeting capability - re-engage POB website visitors
✅ Pros: Conversion tracking with attribution windows (30-day click, 1-day view)
✅ Pros: Lookalike modeling - find similar audiences
✅ Pros: Frequency cap presets (awareness, consideration, conversion)

❌ Cons: Higher CPM ($8.00 vs $5-7) due to audience precision
✅ BUT: CPM is bid-based (auction) - AUTOBID optimizes over time
✅ BUT: Exchange breakdown shows where value is (Yahoo Exchange: 72% viewability)

Audience Match: EXCELLENT
- Yahoo DSP segments = Outdoor enthusiasts + Eco-conscious
- POB Target = EXACT SAME
- Overlap: ~80% (precision audience targeting)
- Segment quality scores: 0.80-0.95 (high quality data)

Reach Efficiency: HIGH
- 2M daily impressions available across 9 exchanges
- With targeting: ~1.6M relevant impressions daily
- Effective CPM: $10 (20% waste vs 80-95% for publishers)
- Brand safety scores: 0.70-0.95 depending on exchange
```

---

### **Newton's Comparative Analysis & Decision**

```markdown
COMPARISON TABLE:

Metric                    | ESPN      | CNN       | Yahoo DSP
--------------------------|-----------|-----------|------------
Daily Reach               | 500K      | 150K      | 2M
Base CPM                  | $5.00     | $7.00     | $8.00 (auction)
Targeting Type            | Placement | Contextual| Audience
Target Audience Match     | Poor (~5%)| Medium (~20%)| Excellent (~80%)
Relevant Impressions/Day  | 25K       | 30K       | 1.6M
Effective CPM             | $100      | $35       | $10
Wasted Impressions        | 95%       | 80%       | 20%
Conversion Tracking       | No        | No        | Yes
Audience Insights         | No        | No        | Yes
Retargeting               | No        | No        | Yes
Optimization              | Manual    | Manual    | Automated

DECISION: Yahoo DSP (100% of budget)

REASONING:

1. AUDIENCE PRECISION IS CRITICAL:
   Performance Outerwear Brand needs to reach a SPECIFIC audience:
   outdoor enthusiasts who value sustainability. This is not a broad
   demographic - it's a defined lifestyle segment.
   
   ESPN reaches sports fans (5% overlap with outdoor enthusiasts)
   CNN reaches climate news readers (20% overlap with gear buyers)
   Yahoo DSP reaches outdoor enthusiasts directly (80% precision)

2. COST EFFICIENCY MATH:
   ESPN: $50K ÷ $5 CPM = 10M impressions
         10M × 5% relevant = 500K target impressions
         Cost per target impression: $100
   
   CNN: $50K ÷ $7 CPM = 7.14M impressions
        7.14M × 20% relevant = 1.43M target impressions
        Cost per target impression: $35
   
   Yahoo DSP: $50K ÷ $8 CPM = 6.25M impressions
              6.25M × 80% relevant = 5M target impressions
              Cost per target impression: $10

   Yahoo DSP delivers 10X more relevant reach than ESPN at 1/10th
   the cost per target customer.

3. MEASURABLE OUTCOMES:
   Yahoo DSP tracks conversions (gear purchases), enabling:
   - ROI measurement
   - Campaign optimization
   - Audience insights
   
   ESPN/CNN cannot measure whether ads drove hiking gear sales.

4. AUDIENCE EXPANSION:
   Yahoo DSP's lookalike modeling can find more customers similar
   to POB's existing buyers. Publishers can't do this.

5. RETARGETING:
   Reach users who visited POB website but didn't purchase.
   Critical for high-consideration outdoor gear purchases.
```

**Newton's Recommendation:**
```
RECOMMENDED STRATEGY: Allocate 100% of $50K budget to Yahoo DSP

RATIONALE:
The target audience for Performance Outerwear Brand is too specific
for broad publisher placements. While ESPN and CNN offer lower base
CPMs, the audience mismatch makes them extremely inefficient.

Yahoo DSP's audience targeting capabilities are perfectly aligned
with POB's target customer:
- "outdoor_enthusiasts" segment (EXACT match)
- "eco_conscious_consumers" segment (EXACT match)  
- "sustainable_shoppers" segment (EXACT match)

The higher CPM ($8.00 vs $5.00) is more than offset by 80%
audience precision vs 5% for ESPN. Effective cost per target
impression is $10 vs $100 - a 10X improvement.

Additionally, conversion tracking will enable us to measure actual
hiking gear purchases and optimize the campaign in real-time.

Expected outcome: 
- 5M relevant impressions (vs 500K on ESPN)
- Measurable conversion tracking
- Audience insights for future campaigns
- 10X better cost efficiency
```

---

### **Act 2: Campaign Execution**

Newton executes the buy on Yahoo DSP with precision audience targeting.

```python
# Step 1: Sync Creative
mcp_yahoo.sync_creatives(
    creatives=[
        {
            "creative_id": "pob_sustainable_hiking_300x250",
            "name": "Performance Outerwear Brand - Sustainable Hiking Collection",
            "format_id": "display_300x250",
            "click_through_url": "https://performanceouterwear.com/sustainable-hiking",
            "preview_url": "https://cdn.performanceouterwear.com/ad_sustainable_hiking.jpg",
            "assets": {
                "image": {
                    "url": "https://cdn.performanceouterwear.com/ad_sustainable_hiking.jpg",
                    "width": 300,
                    "height": 250
                }
            }
        }
    ]
)

# Step 2: Create Media Buy with Audience Targeting
mcp_yahoo.create_media_buy(
    buyer_ref="pob_yahoo_sustainable_hiking_dec_2025",
    brand_manifest={
        "name": "Performance Outerwear Brand",
        "url": "https://performanceouterwear.com"
    },
    start_time="2025-12-01T00:00:00Z",
    end_time="2025-12-31T23:59:59Z",
    packages=[{
        "package_id": "pob_audience_campaign",
        "product_id": "yahoo_display_300x250",
        "budget": 50000,
        "impressions": 6250000,  # $50K ÷ $8 CPM
        "creative_ids": ["pob_sustainable_hiking_300x250"],
        "pacing": "even",
        "pricing_option_id": "cpm_usd_auction",
        
        # KEY: Audience targeting overlay
        "targeting_overlay": {
            "audiences_any_of": [
                "outdoor_enthusiasts",        # PRIMARY
                "eco_conscious_consumers",    # PRIMARY
                "adventure_travelers",        # SECONDARY
                "sustainable_shoppers"        # SECONDARY
            ],
            "signals": [
                "hiking_gear_interest",
                "camping_equipment_research",
                "sustainable_products_affinity"
            ],
            "geo_country_any_of": ["US"]
        }
    }]
)
```

**Yahoo DSP Response:**

> **Note:** Yahoo DSP uses specific terminology aligned with their API:
> - **Campaign** = Order (contains multiple Lines)
> - **Line** = Ad Group (targeting + budget + bidding)
> - **Ad** = Creative assignment
> - Status values: `ACTIVE`, `PENDING_REVIEW`, `PAUSED`, `STOP_DAILY_BUDGET`, etc.

```json
{
  "status": "pending",
  "media_buy_id": "yahoo_dsp_pob_20251201",
  "external_ids": {
    "yahoo_campaign_id": "yahoo_dsp_pob_20251201",
    "yahoo_order_id": 567890,
    "line_ids": [1234567]
  },
  "packages": [{
    "package_id": "pob_audience_campaign",
    "status": "pending",
    "external_id": "1234567"  // Yahoo DSP Line ID
  }],
  
  // Full Line details (Yahoo DSP API structure):
  "lines": [{
    "id": 1234567,
    "name": "Performance Outerwear Brand - pob_audience_campaign",
    "orderId": 567890,
    "mediaType": "DISPLAY",
    "status": "PENDING_REVIEW",
    
    // Dates
    "startDate": "2025-12-01",
    "endDate": "2025-12-31",
    
    // Budget (Yahoo DSP style)
    "scheduleBudget": 50000,
    "dailyBudget": 1612.90,
    
    // Enhanced Bidding Configuration (Yahoo DSP API)
    "biddingConfig": {
      "bidStrategy": "AUTOBID",
      "bidType": "DYNAMIC",
      "goalType": "CLICK",
      "maxBid": 8.00,
      "pacingType": "EVEN",
      
      // Learning phase tracking (new!)
      "learningPhase": {
        "enabled": true,
        "durationDays": 3,
        "minDataPoints": 100,
        "status": "NOT_STARTED"
      },
      
      // Pacing details
      "pacingDetails": {
        "algorithm": "time_weighted",
        "dailyBudget": 1612.90,
        "overspendAllowed": false
      },
      
      // Bid adjustments (AUTOBID feature)
      "bidAdjustments": {
        "enabled": true,
        "maxAdjustment": 0.50,
        "factors": {
          "deviceType": {"mobile": 1.1, "desktop": 1.0, "ctv": 1.2},
          "dayOfWeek": {"weekday": 1.0, "weekend": 0.95},
          "timeOfDay": {"evening": 1.15, "night": 0.8}
        }
      },
      
      // Target CTR for CLICK goal type
      "targetCtr": 0.001
    },
    
    // Enhanced Frequency Cap (with presets)
    "frequencyCap": {
      "type": "IMPRESSION",
      "limit": 3,
      "duration": 1,
      "durationUnit": "DAY",
      "scope": "LINE",
      "effectivePeriodSeconds": 86400,
      "description": "Max 3 impressions per user per 1 day(s) at line level"
    },
    
    // Exchanges targeted (with metadata)
    "exchanges": ["YAHOO_EXCHANGE", "INDEX_EXCHANGE", "MAGNITE", "OPEN_EXCHANGE"],
    
    // Audience segments with Yahoo DSP metadata
    "audienceSegments": [
      {
        "id": "seg_12345",
        "name": "Outdoor Enthusiasts",
        "type": "YAHOO_OWNED",
        "provider": "Yahoo",
        "reach": 3500000,
        "cpmLift": 0.25,
        "recency": "30_DAYS",
        "qualityScore": 0.89
      },
      {
        "id": "seg_23456",
        "name": "Eco Conscious Consumers",
        "type": "THIRD_PARTY",
        "provider": "Oracle Data Cloud",
        "reach": 2800000,
        "cpmLift": 0.30,
        "recency": "60_DAYS",
        "qualityScore": 0.85
      },
      {
        "id": "seg_34567",
        "name": "Adventure Travelers",
        "type": "YAHOO_OWNED",
        "provider": "Yahoo",
        "reach": 1900000,
        "cpmLift": 0.28,
        "recency": "45_DAYS",
        "qualityScore": 0.82
      },
      {
        "id": "seg_45678",
        "name": "Sustainable Shoppers",
        "type": "THIRD_PARTY",
        "provider": "Experian",
        "reach": 1500000,
        "cpmLift": 0.35,
        "recency": "30_DAYS",
        "qualityScore": 0.80
      }
    ]
  }],
  
  // Reach estimate
  "reachEstimate": {
    "estimatedUniqueUsers": 5200000,
    "estimatedImpressions": 18200000,
    "estimatedDailyImpressions": 586000,
    "confidence": 0.87
  },
  
  // Bid landscape data:
  "bidLandscape": {
    "medianWinningBid": 8.40,
    "percentile25": 6.72,
    "percentile75": 10.00,
    "percentile90": 12.00,
    "competitionLevel": "MEDIUM",
    "estimatedWinRateAtBid": {
      "$6.40": 0.25,
      "$8.00": 0.45,
      "$9.60": 0.65,
      "$12.00": 0.85
    }
  }
}
```

**Newton's Observation:**
```
Yahoo DSP Campaign Analysis:

AUDIENCE VALIDATION:
✅ Total addressable audience: 5.2M users
✅ Estimated unique reach: 4.16M users
✅ Segment quality scores: 0.80-0.89 (high quality)
✅ Segment providers: Yahoo (owned) + Oracle + Experian (third-party)

COMPETITIVE LANDSCAPE:
- Median winning bid: $8.40 (our max bid: $8.00)
- Estimated win rate at $8.00: 45%
- Competition level: MEDIUM
- Bid landscape shows $9.60 would achieve 65% win rate

BIDDING STRATEGY CONFIGURED:
- Strategy: AUTOBID (dynamic optimization)
- Goal type: CLICK (optimize for CTR)
- Target CTR: 0.1%
- Learning phase: 3 days, 100 data points minimum
- Bid adjustments enabled: +10% mobile, +20% CTV, +15% evening

EXCHANGE STRATEGY:
Targeting 4 exchanges for optimal reach/quality balance:
- YAHOO_EXCHANGE: Premium owned inventory (72% viewability, 0.95 brand safety)
- INDEX_EXCHANGE: Header bidding SSP (71% viewability)
- MAGNITE: Premium publishers (ESPN, CNN, NYT access)
- OPEN_EXCHANGE: Scale inventory (lower viewability, requires filtering)

FREQUENCY CAP:
- Preset: "consideration" (3 impressions/user/day at LINE level)
- Prevents ad fatigue while maintaining reach

STRATEGY CONFIRMATION:
The audience segments are EXACTLY aligned with POB's target:
- outdoor_enthusiasts: 3.5M reach, Yahoo-owned data (PRIMARY)
- eco_conscious_consumers: 2.8M reach, Oracle Data Cloud (PRIMARY)
- Combined quality score: 0.85+ (excellent)

AUTOBID will optimize bids between $6-10 to maximize clicks within budget.
Learning phase will complete in ~3 days with bid adjustment refinements.

Campaign pending review. Expected approval within 24 hours.
```

---

### **Act 3: Performance Monitoring (Week 2)**

Newton checks performance after 2 weeks to evaluate the audience-targeted approach.

```python
mcp_yahoo.get_media_buy_delivery(
    media_buy_ids=["yahoo_dsp_pob_20251201"],
    start_date="2025-12-01",
    end_date="2025-12-14"
)
```

**Yahoo DSP Performance Report:**

> **Yahoo DSP Reporting API** provides detailed metrics at Line level with
> DSP-specific dimensions (exchange breakdown, device breakdown, win rate, viewability).
> 29 metrics available across volume, cost, rate, quality, auction, and reach categories.

```json
{
  "packages": [{
    "package_id": "pob_audience_campaign",
    "external_id": "1234567",
    "status": "delivering",
    
    // Standard AdCP metrics:
    "impressions": 3100000,
    "clicks": 34100,
    "spend": 24800.00,
    
    // Yahoo DSP Line-level metrics (in metadata):
    "metadata": {
      // Line info (Yahoo DSP terminology)
      "lineId": 1234567,
      "lineName": "Performance Outerwear Brand - pob_audience_campaign",
      "lineStatus": "ACTIVE",
      "mediaType": "DISPLAY",
      "goalType": "CLICK",
      
      // Bidding performance (DSP-specific)
      "bidRequests": 10800000,
      "bidsSubmitted": 8640000,
      "bidsWon": 3100000,
      "winRate": 0.287,
      "avgBid": 8.00,
      "avgWinPrice": 8.00,
      
      // Performance metrics
      "ctr": 0.011,
      "conversions": 682,
      "conversionRate": 0.020,
      "cpm": 8.00,
      "cpc": 0.73,
      "cpa": 36.36,
      
      // Viewability metrics (MRC standard)
      "viewableImpressions": 2325000,
      "viewabilityRate": 0.75,
      "measurableImpressions": 2945000,
      "measurabilityRate": 0.95,
      
      // Reach metrics (new!)
      "uniqueUsers": 886000,
      "frequency": 3.5,
      
      // Budget tracking
      "scheduleBudget": 50000,
      "dailyBudget": 1612.90,
      "spend": 24800.00,
      "budgetUtilization": 0.496,
      "budgetRemaining": 25200.00,
      
      // Cost breakdown (new!)
      "mediaCost": 21080.00,
      "dataFees": 2480.00,
      "platformFees": 1240.00,
      
      // Audience segments active
      "audienceSegments": 4,
      
      // Enhanced Exchange breakdown (with per-exchange metrics)
      "exchangeBreakdown": {
        "YAHOO_EXCHANGE": {
          "exchangeId": 1,
          "exchangeName": "Yahoo Exchange",
          "exchangeType": "owned",
          "impressions": 1395000,
          "viewableImpressions": 1004400,
          "viewabilityRate": 0.72,
          "clicks": 16740,
          "ctr": 0.012,
          "avgCpm": 6.50,
          "spend": 9067.50,
          "fraudRate": 0.02,
          "brandSafetyScore": 0.95
        },
        "INDEX_EXCHANGE": {
          "exchangeId": 5,
          "exchangeName": "Index Exchange",
          "exchangeType": "ssp",
          "impressions": 930000,
          "viewableImpressions": 660300,
          "viewabilityRate": 0.71,
          "clicks": 10230,
          "ctr": 0.011,
          "avgCpm": 7.50,
          "spend": 6975.00,
          "fraudRate": 0.04,
          "brandSafetyScore": 0.90
        },
        "MAGNITE": {
          "exchangeId": 3,
          "exchangeName": "Magnite (Rubicon)",
          "exchangeType": "ssp",
          "impressions": 465000,
          "viewableImpressions": 316200,
          "viewabilityRate": 0.68,
          "clicks": 4185,
          "ctr": 0.009,
          "avgCpm": 8.50,
          "spend": 3952.50,
          "fraudRate": 0.05,
          "brandSafetyScore": 0.88
        },
        "OPEN_EXCHANGE": {
          "exchangeId": 99,
          "exchangeName": "Open RTB Marketplace",
          "exchangeType": "open",
          "impressions": 310000,
          "viewableImpressions": 170500,
          "viewabilityRate": 0.55,
          "clicks": 2945,
          "ctr": 0.0095,
          "avgCpm": 4.00,
          "spend": 1240.00,
          "fraudRate": 0.12,
          "brandSafetyScore": 0.70
        }
      },
      
      // Device breakdown (new!)
      "deviceBreakdown": {
        "mobile": {
          "impressions": 1705000,
          "clicks": 20460,
          "ctr": 0.012,
          "share": 0.55
        },
        "desktop": {
          "impressions": 930000,
          "clicks": 9300,
          "ctr": 0.010,
          "share": 0.30
        },
        "tablet": {
          "impressions": 248000,
          "clicks": 2232,
          "ctr": 0.009,
          "share": 0.08
        },
        "ctv": {
          "impressions": 155000,
          "clicks": 1705,
          "ctr": 0.011,
          "share": 0.05
        },
        "other": {
          "impressions": 62000,
          "clicks": 403,
          "ctr": 0.0065,
          "share": 0.02
        }
      }
    }
  }],
  
  // Totals
  "totals": {
    "impressions": 3100000,
    "clicks": 34100,
    "spend": 24800.00
  }
}
```

**Segment-Level Performance (Yahoo DSP Audience Insights):**
```json
{
  "audienceInsights": {
    "topPerformingSegment": "outdoor_enthusiasts",
    "segmentPerformance": {
      "outdoor_enthusiasts": {
        "type": "YAHOO_OWNED",
        "provider": "Yahoo",
        "impressions": 1400000,
        "clicks": 19600,
        "ctr": 0.014,
        "conversions": 372,
        "conversionRate": 0.019
      },
      "eco_conscious_consumers": {
        "type": "THIRD_PARTY",
        "provider": "Oracle Data Cloud",
        "impressions": 900000,
        "clicks": 9900,
        "ctr": 0.011,
        "conversions": 198,
        "conversionRate": 0.020
      },
      "adventure_travelers": {
        "type": "YAHOO_OWNED",
        "provider": "Yahoo",
        "impressions": 500000,
        "clicks": 3000,
        "ctr": 0.006,
        "conversions": 72,
        "conversionRate": 0.024
      },
      "sustainable_shoppers": {
        "type": "THIRD_PARTY",
        "provider": "Experian",
        "impressions": 300000,
        "clicks": 1600,
        "ctr": 0.005,
        "conversions": 40,
        "conversionRate": 0.025
      }
    },
    
    // Optimization insights (AUTOBID adjustments):
    "bidOptimization": {
      "optimalBid": 7.85,
      "bidAdjustments": {
        "outdoor_enthusiasts": "+15%",
        "sustainable_shoppers": "+20%",
        "adventure_travelers": "+10%",
        "eco_conscious_consumers": "0%"
      }
    }
  }
}
```

---

### **Act 4: Newton's Strategic Analysis**

**Newton's Deep Performance Analysis:**

```markdown
# Performance Outerwear Brand Campaign Analysis - Week 2

## Campaign Overview
- Platform: Yahoo DSP (100% of budget)
- Budget: $50,000
- Spend to date: $24,800 (49.6% of budget)
- Duration: 14 days of 31 (45% elapsed)
- Status: AHEAD OF SCHEDULE

## Performance Results

### Volume Metrics
- Impressions: 3.1M (50% of goal, ON TRACK)
- Clicks: 34,100 (1.1% CTR - EXCELLENT)
- Conversions: 682 gear purchases (MEASURABLE ROI)

### Cost Efficiency
- Avg CPM: $8.03 (bid-based, stable)
- Cost per click: $0.73 ($24,800 / 34,100 clicks)
- Cost per conversion: $36.36 ($24,800 / 682 conversions)

### Quality Metrics
- Viewability: 75% (HIGH - impressions were actually seen)
- Measurability: 95% (excellent measurement coverage)
- Win rate: 28.7% (won ~3M of 10.8M auction opportunities)
- CTR: 1.1% (2X industry average of 0.5%)

### Reach Metrics (NEW)
- Unique users: 886K (reached nearly 1M people)
- Frequency: 3.5 impressions/user (within 3/day cap)

### Cost Breakdown (NEW)
- Media cost: $21,080 (85% of spend)
- Data fees: $2,480 (10% - audience segment costs)
- Platform fees: $1,240 (5%)

### Exchange Performance (NEW)
| Exchange | Impressions | Viewability | CTR | Brand Safety |
|----------|-------------|-------------|-----|--------------|
| Yahoo Exchange | 1.4M (45%) | 72% | 1.2% | 0.95 |
| Index Exchange | 930K (30%) | 71% | 1.1% | 0.90 |
| Magnite | 465K (15%) | 68% | 0.9% | 0.88 |
| Open RTB | 310K (10%) | 55% | 0.95% | 0.70 |

KEY INSIGHT: Yahoo Exchange delivers highest CTR (1.2%) and brand safety.
Consider increasing Yahoo Exchange allocation in optimization.

### Device Performance (NEW)
| Device | Impressions | CTR | Share |
|--------|-------------|-----|-------|
| Mobile | 1.7M | 1.2% | 55% |
| Desktop | 930K | 1.0% | 30% |
| Tablet | 248K | 0.9% | 8% |
| CTV | 155K | 1.1% | 5% |

KEY INSIGHT: Mobile driving best performance (1.2% CTR).
AUTOBID bid adjustment (+10% mobile) is working.

## Audience Insights (KEY FINDING)

The audience-targeted approach VALIDATED:

### Segment Performance Ranking:

1. **outdoor_enthusiasts** (BEST VOLUME)
   - 1.4M impressions, 19.6K clicks (1.4% CTR)
   - 372 conversions, 1.9% conversion rate
   - STATUS: Primary driver of results

2. **sustainable_shoppers** (BEST CONVERSION RATE)
   - 300K impressions, 1.6K clicks (0.5% CTR)
   - 40 conversions, 2.5% conversion rate ← HIGHEST
   - STATUS: Small but HIGHLY qualified audience

3. **adventure_travelers** (BEST BALANCE)
   - 500K impressions, 3K clicks (0.6% CTR)
   - 72 conversions, 2.4% conversion rate
   - STATUS: High conversion efficiency

4. **eco_conscious_consumers** (MODERATE)
   - 900K impressions, 9.9K clicks (1.1% CTR)
   - 198 conversions, 2.0% conversion rate
   - STATUS: Solid performance, good volume

## Algorithmic Optimization Working

Yahoo DSP's AUTOBID made intelligent adjustments after learning phase:

### Learning Phase Status: COMPLETED ✅
- Duration: 3 days
- Data points collected: 847 (exceeded 100 minimum)
- Status: Algorithm now fully optimized

### Bid Adjustments Applied:
| Factor | Adjustment | Reason |
|--------|------------|--------|
| outdoor_enthusiasts | +15% | Best volume driver |
| sustainable_shoppers | +20% | Highest conversion rate |
| Mobile device | +10% | Best CTR (1.2%) |
| Evening hours | +15% | Peak engagement time |
| Weekend | -5% | Lower conversion rate |
| Open Exchange | -10% | Lower viewability (55%) |

### Results:
- Found optimal bid: $7.85 (vs initial $8.00 max)
- Bid range used: $6.28 - $9.42 (within $6-10 range)
- Result: 2% cost savings while maintaining reach
- Win rate improved: 28.7% → 31.2% (after optimization)

## Comparative Analysis: What If We'd Chosen ESPN?

### ESPN Projection (Hypothetical):
- Budget: $24,800 spent
- CPM: $5.00 (fixed)
- Impressions: 4.96M (59% more impressions!)
- Relevant impressions: 248K (5% audience match)
- Estimated clicks: 1,240 (0.5% CTR)
- Estimated conversions: 25 (2% conversion rate)
- Cost per conversion: $992

### Yahoo DSP Actual:
- Impressions: 3.1M (38% FEWER impressions)
- Relevant impressions: 2.48M (80% audience match = 10X MORE relevant reach)
- Clicks: 34,100 (27X MORE clicks)
- Conversions: 682 (27X MORE conversions)
- Cost per conversion: $36.36 (27X LOWER cost)

**KEY INSIGHT:** 
ESPN would have delivered MORE total impressions (4.96M vs 3.1M)
but FEWER relevant impressions (248K vs 2.48M). Audience targeting
delivered 10X more relevant reach despite lower total volume.

## ROI Calculation

Assumptions:
- Average order value: $150 (hiking jacket/pants)
- Profit margin: 40% ($60 profit per sale)

Results:
- 682 conversions × $150 AOV = $102,300 in revenue
- 682 conversions × $60 profit = $40,920 in gross profit
- Campaign spend: $24,800
- Net profit: $16,120
- ROI: 65% ($16,120 / $24,800)

**Campaign is PROFITABLE at week 2 mark.**

If trend continues:
- Projected conversions (full 31 days): ~1,500
- Projected revenue: ~$225,000
- Projected profit: ~$90,000
- Projected net profit: ~$40,000
- Projected ROI: 80%

## Strategic Recommendations

### Option A: Stay the Course ✅ RECOMMENDED
- Current strategy is working exceptionally well
- All audience segments performing
- Algorithm optimizing bids effectively
- Campaign is profitable
- Action: Continue with no changes

### Option B: Budget Increase (If Available)
- Performance justifies increased investment
- Current ROI: 65% (highly profitable)
- Could increase budget by 50% ($25K → $75K total)
- Expected: Maintain profitability at scale

### Option C: Audience Refinement
- "sustainable_shoppers" has HIGHEST conversion rate (2.5%)
- Consider creating dedicated campaign for this segment
- Allocate 20% of remaining budget to pure sustainability focus
- Test: Sustainability-focused creative messaging

### Option D: Lookalike Expansion
- Yahoo DSP can create lookalike audiences from converters
- Find similar users to the 682 people who purchased
- Expand addressable audience by 2-3X
- Risk: Lower quality, but worth testing with 10-20% of budget

## Key Learnings

1. **Audience Targeting Delivers ROI**
   - 80% precision vs 5% for broad placement
   - 27X more conversions than ESPN would deliver
   - 27X lower cost per conversion

2. **Higher CPM Can Mean Lower Cost**
   - Yahoo DSP: $8 CPM → $36.36 cost per conversion
   - ESPN (projected): $5 CPM → $992 cost per conversion
   - Precision beats price

3. **Measurement Enables Optimization**
   - Conversion tracking shows ROI
   - Segment insights guide strategy
   - Auto-bidding improves efficiency
   - ESPN couldn't provide any of this data

4. **Small Audiences Can Outperform**
   - "sustainable_shoppers" = smallest segment (300K impressions)
   - "sustainable_shoppers" = HIGHEST conversion rate (2.5%)
   - Quality > Quantity

## Recommended Action

✅ CONTINUE YAHOO DSP STRATEGY

The audience-targeted approach is working exactly as predicted:
- Reaching the right people (outdoor enthusiasts + eco-conscious)
- Driving measurable conversions (682 gear purchases)
- Delivering profitable ROI (65% at week 2, projecting 80% at completion)
- Enabling ongoing optimization (algorithm improving bids)

NO changes needed. Let the campaign run its course.
```

---

## 🎭 Demo Flow Summary

### **What Newton Demonstrates:**

1. **Audience-First Thinking**
   - Recognizes POB needs a SPECIFIC audience
   - Rejects broad placement strategies (ESPN)
   - Prioritizes audience match over CPM

2. **Strategic Comparison**
   - Queries multiple agents systematically
   - Calculates effective CPM (accounts for waste)
   - Makes data-driven recommendation with clear math

3. **Precision Execution**
   - Configures audience targeting (4 segments)
   - Enables auto-optimization (bid strategy)
   - Sets up conversion tracking

4. **Performance Intelligence**
   - Interprets rich DSP metrics
   - Identifies best-performing segments
   - Compares actual results vs ESPN projection (27X better!)
   - Calculates ROI ($16K profit at week 2)

5. **Strategic Insights**
   - Small audiences can outperform (sustainable_shoppers)
   - Higher CPM ≠ higher cost (precision reduces waste)
   - Measurement enables optimization

---

## 💡 Key Demo Talking Points

### **For Audience:**

1. **"Newton understands audience strategy"**
   - Not just "buy cheapest inventory"
   - Recognizes when audience precision matters
   - Calculates effective cost, not just CPM
   - Evaluates segment quality scores and data providers

2. **"Newton makes the math work"**
   - ESPN: $5 CPM = $100 effective CPM (95% waste)
   - Yahoo DSP: $8 CPM = $10 effective CPM (20% waste)
   - 10X cost efficiency through targeting
   - Cost breakdown transparency (media 85%, data 10%, platform 5%)

3. **"Newton leverages programmatic advantages"**
   - 4 audience segments with provider metadata (Yahoo, Oracle, Experian)
   - 9 exchanges with quality metrics (viewability, brand safety, fraud rate)
   - AUTOBID optimization with learning phase (3 days, 100+ data points)
   - Bid adjustments by device (+10% mobile), time (+15% evening), exchange
   - Conversion tracking (682 measurable purchases)
   - Segment insights (sustainable_shoppers = best conversion rate)

4. **"Newton proves ROI with rich reporting"**
   - Week 2: 65% ROI ($16K profit on $24.8K spend)
   - Projected: 80% ROI at campaign completion
   - ESPN would have delivered 1/27th the conversions
   - Exchange breakdown shows Yahoo Exchange = best CTR (1.2%)
   - Device breakdown shows Mobile = best performance (55% share, 1.2% CTR)
   - Reach metrics: 886K unique users at 3.5 frequency

5. **"AdCP protocol enables all of this"**
   - Same tools work across publisher (ESPN) and DSP (Yahoo)
   - Newton doesn't need to know implementation details
   - Audience capabilities surfaced through product responses
   - Yahoo DSP API terminology exposed (Lines, AUTOBID, goalType)

---

## 🚀 Running the Demo

### **Setup (Before Demo):**

1. Ensure services running:
   ```bash
   aws ecs describe-services --cluster salesagent-espn --services salesagent-espn --region us-east-1
   aws ecs describe-services --cluster salesagent-cnn --services salesagent-cnn --region us-east-1
   aws ecs describe-services --cluster salesagent-yahoo --services salesagent-yahoo --region us-east-1
   ```

2. Verify Newton has MCP servers registered:
   - `mcp_espn` → `http://espn.salesagent.local:9580/mcp`
   - `mcp_cnn` → `http://cnn.salesagent.local:9580/mcp`
   - `mcp_yahoo` → `http://yahoo.salesagent.local:9580/mcp`

3. Clean previous demo data (optional):
   ```python
   mcp_espn.clean_demo_data(tenant_id="espn")
   mcp_cnn.clean_demo_data(tenant_id="cnn")
   mcp_yahoo.clean_demo_data(tenant_id="yahoo")
   ```

### **Demo Execution:**

Run Newton with the scenario prompt:

```
PROMPT: "I'm planning a campaign for Performance Outerwear Brand to launch 
their new sustainable hiking collection. Budget: $50K for 31 days in December.

Target audience (pre-identified through analysis):
- Outdoor enthusiasts (hiking, camping, trail running)
- Eco-conscious consumers who value sustainability
- Age 25-45, household income $75K+
- Active lifestyle, weekend adventurers

Compare inventory options across ESPN, CNN, and Yahoo DSP. Determine which 
platform can BEST REACH this specific audience. Make a strategic recommendation, 
execute the buy, and after 2 weeks analyze performance to validate the strategy."
```

Newton will:
1. Call `get_products` on ESPN, CNN, and Yahoo DSP
2. Analyze audience match for each platform
3. Calculate effective CPM (accounting for waste)
4. Recommend Yahoo DSP based on audience precision
5. Execute `sync_creatives` + `create_media_buy` with audience targeting
6. Call `get_media_buy_delivery` after simulated 2 weeks
7. Analyze segment performance and ROI
8. Compare actual results vs ESPN projection (27X better)

---

## 📊 Expected Demo Outcomes

### **Audience Takeaways:**

1. ✅ **Newton makes intelligent strategic decisions**
   - Not just executing orders
   - Analyzing audience fit with segment quality scores
   - Calculating true cost efficiency
   - Evaluating exchange quality (viewability, brand safety)
   
2. ✅ **Audience targeting has measurable value**
   - 10X more relevant reach (2.48M vs 248K)
   - 27X more conversions (682 vs 25 projected)
   - 27X lower cost per conversion ($36 vs $992)
   - 886K unique users reached at optimal frequency
   
3. ✅ **Higher CPM can mean lower cost**
   - $8 CPM with 80% precision = $10 effective
   - $5 CPM with 5% precision = $100 effective
   - Precision beats price
   - Cost transparency: media 85%, data fees 10%, platform 5%
   
4. ✅ **Yahoo DSP delivers unique value**
   - Audience segments with provider metadata (Yahoo, Oracle, Experian)
   - 9 exchanges with quality metrics
   - AUTOBID with learning phase and bid adjustments
   - Conversion tracking (682 measurable purchases)
   - Segment insights (sustainable_shoppers = best conversion rate)
   - Exchange insights (Yahoo Exchange = best CTR)
   - Device insights (Mobile = 55% share, best performance)
   
5. ✅ **AdCP protocol is flexible**
   - Same tools work for publisher and DSP
   - Audience capabilities surfaced naturally
   - Yahoo DSP API terminology exposed (Lines, AUTOBID, goalType)
   - Rich reporting dimensions (exchange, device, audience)
   - Newton adapts strategy to product responses

---

## 📝 Demo Notes

**Preparation time:** 5 minutes  
**Demo duration:** 12-18 minutes (live)  
**Technical level:** Medium (assumes AdCP knowledge)

**Key moments to emphasize:**
1. Newton's audience match analysis (ESPN: 5%, Yahoo: 80%)
2. Effective CPM calculation ($100 vs $10)
3. Exchange selection with quality metrics (viewability, brand safety)
4. AUTOBID learning phase and bid adjustments
5. Week 2 results: 682 conversions, 65% ROI
6. Exchange breakdown: Yahoo Exchange = best CTR (1.2%)
7. Device breakdown: Mobile = best performance (55% share)
8. ESPN comparison: 27X better performance

**New features to highlight:**
- 9 exchanges with rich metadata (avgCpm, viewabilityRate, brandSafetyScore)
- AUTOBID with learning phase (3 days, 100 data points)
- Bid adjustments by device, time, exchange
- Frequency cap presets (awareness, consideration, conversion)
- Cost breakdown (media, data fees, platform fees)
- 29 reporting metrics across 4 dimensions

**Backup plan:** Pre-recorded responses if live demo fails

---

This demo powerfully demonstrates Newton's intelligence in audience strategy and Yahoo DSP's unique programmatic value aligned with the actual Yahoo DSP API! 🏔️🚀
