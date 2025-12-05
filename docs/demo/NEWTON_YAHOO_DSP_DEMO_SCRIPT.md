# Newton + Yahoo DSP Demo Script

## 🎯 Demo Objective

Show Newton executing a media buy on **Yahoo DSP** using **native Yahoo audience tools**, demonstrating:
1. **Strategic execution** - Newton receives allocation from MMM/audience modeling
2. **Native tool integration** - Newton uses Yahoo's `getAudienceSegments` and `Get_analytics_for_audiences_segment`
3. **Intelligent segment selection** - Newton evaluates and selects optimal audiences
4. **AdCP interoperability** - Standard AdCP tools work alongside native DSP tools

---

## 📋 Demo Scenario

**Advertiser:** Honda  
**Campaign:** CR-V Spring Launch Q1 2026  
**Budget:** $500K allocated to Yahoo DSP (determined by Media Mix Model)

**Strategic Context:**
- Honda's MMM determined that $500K should go to Yahoo DSP for programmatic reach
- Audience modeling identified target: Auto intenders considering SUVs, age 25-54
- Newton's job: Operationalize this allocation by finding the RIGHT audiences within Yahoo DSP

**Newton's Task:**
- Use Yahoo DSP's native audience tools to discover available segments
- Evaluate segment quality (reach, CPM, conversion rates)
- Select optimal segment mix aligned with campaign objectives
- Execute the buy using standard AdCP tools

---

## 🎬 Demo Script

### **Act 1: Strategic Brief**

Newton receives instructions from Honda's agency with pre-determined allocation.

```python
# Newton receives strategic brief:
brief = {
    "advertiser": "Honda",
    "campaign": "CR-V Spring Launch 2026",
    "budget": 500000,
    "currency": "USD",
    "platform": "yahoo_dsp",
    "allocation_source": "Media Mix Model Q4 2025",
    
    "target_audience": {
        "description": "Auto intenders considering SUVs, age 25-54",
        "source": "Audience modeling from dealer data + 3P signals",
        "key_attributes": [
            "In-market for SUV/Crossover",
            "Household income $75K+",
            "Age 25-54",
            "Competitive brand considerers (Toyota RAV4, Subaru Outback)"
        ]
    },
    
    "objectives": {
        "primary": "awareness",
        "secondary": "dealer_visits",
        "kpis": ["reach", "frequency", "viewability", "dealer_visit_rate"]
    },
    
    "flight": {
        "start": "2026-01-01",
        "end": "2026-03-31"
    }
}
```

**Newton's Internal Reasoning:**
```
"I have a $500K allocation for Yahoo DSP from Honda's MMM. The audience 
modeling team identified auto intenders 25-54 as the target. My job is to:

1. DISCOVER what audience segments Yahoo DSP has available
2. EVALUATE which segments best match Honda's target audience
3. SELECT the optimal segment mix across the funnel
4. EXECUTE the buy using AdCP tools

Let me start by querying Yahoo DSP's audience inventory..."
```

---

### **Act 2: Audience Discovery**

Newton uses Yahoo DSP's native `getAudienceSegments` tool to discover available audiences.

```python
# Step 1: Query INTEREST segments (Yahoo behavioral data)
mcp_yahoo.getAudienceSegments(
    accountId=12345,  # Honda's advertiser ID
    segmentType="INTEREST",
    keywords="auto, SUV, crossover, vehicle, car shopping",
    status="ACTIVE",
    countryCodes="USA",
    limit=25
)

# Step 2: Query FACT segments (third-party data providers)
mcp_yahoo.getAudienceSegments(
    accountId=12345,
    segmentType="FACT",
    keywords="auto intender, vehicle purchase, dealership, SUV buyer",
    status="ACTIVE",
    countryCodes="USA",
    limit=25
)

# Step 3: Query LOOKALIKE segments (based on Honda converters)
mcp_yahoo.getAudienceSegments(
    accountId=12345,
    segmentType="LOOKALIKE",
    query="Honda",
    status="ACTIVE",
    limit=10
)

# Step 4: Query CONVERSIONRULE segments (Honda pixel-based)
mcp_yahoo.getAudienceSegments(
    accountId=12345,
    segmentType="CONVERSIONRULE",
    status="ACTIVE",
    limit=10
)
```

---

#### **Yahoo DSP Response: INTEREST Segments**

```json
{
  "segments": [
    {
      "id": 98765,
      "name": "Auto Intenders - SUV/Crossover",
      "segmentType": "INTEREST",
      "status": "ACTIVE",
      "reach": 8500000,
      "description": "Users actively researching SUVs and crossovers based on Yahoo search and content consumption",
      "recency": "30_DAYS",
      "cpmLift": 0.15
    },
    {
      "id": 98770,
      "name": "Auto Enthusiasts - New Vehicle Research",
      "segmentType": "INTEREST",
      "status": "ACTIVE",
      "reach": 12000000,
      "description": "Users consuming automotive content and comparing vehicles",
      "recency": "45_DAYS",
      "cpmLift": 0.10
    },
    {
      "id": 98771,
      "name": "Family Vehicle Shoppers",
      "segmentType": "INTEREST",
      "status": "ACTIVE",
      "reach": 6200000,
      "description": "Users researching family-friendly vehicles, safety ratings, cargo space",
      "recency": "30_DAYS",
      "cpmLift": 0.18
    }
  ],
  "totalCount": 47,
  "page": 1
}
```

---

#### **Yahoo DSP Response: FACT Segments (Third-Party Data)**

```json
{
  "segments": [
    {
      "id": 98766,
      "name": "Competitive Auto - Toyota/Subaru Considerers",
      "segmentType": "FACT",
      "status": "ACTIVE",
      "reach": 3200000,
      "provider": "Oracle Data Cloud",
      "description": "Users who have shown purchase intent for Toyota RAV4, Subaru Outback, Forester",
      "recency": "60_DAYS",
      "cpmLift": 0.35,
      "dataFee": 1.50
    },
    {
      "id": 98768,
      "name": "In-Market Auto - Near Purchase (90 days)",
      "segmentType": "FACT",
      "status": "ACTIVE",
      "reach": 2100000,
      "provider": "Polk/IHS Markit",
      "description": "Users predicted to purchase a vehicle within 90 days based on registration and financial data",
      "recency": "30_DAYS",
      "cpmLift": 0.65,
      "dataFee": 2.50
    },
    {
      "id": 98772,
      "name": "SUV/Crossover Intenders - Premium",
      "segmentType": "FACT",
      "status": "ACTIVE",
      "reach": 4800000,
      "provider": "Experian",
      "description": "High-confidence SUV purchase intenders based on credit and lifestyle data",
      "recency": "45_DAYS",
      "cpmLift": 0.45,
      "dataFee": 2.00
    }
  ],
  "totalCount": 23,
  "page": 1
}
```

---

#### **Yahoo DSP Response: LOOKALIKE Segments**

```json
{
  "segments": [
    {
      "id": 98767,
      "name": "Honda Website Converters - Lookalike",
      "segmentType": "LOOKALIKE",
      "status": "ACTIVE",
      "reach": 5100000,
      "seedAudience": "Honda.com build & price completers",
      "seedSize": 125000,
      "similarityScore": 0.85,
      "description": "Users similar to those who completed build & price on Honda.com",
      "recency": "FRESH",
      "cpmLift": 0.25
    },
    {
      "id": 98773,
      "name": "Honda Dealer Visitors - Lookalike",
      "segmentType": "LOOKALIKE",
      "status": "ACTIVE",
      "reach": 3800000,
      "seedAudience": "Honda dealer website visitors",
      "seedSize": 85000,
      "similarityScore": 0.82,
      "description": "Users similar to those who visited Honda dealer websites",
      "recency": "FRESH",
      "cpmLift": 0.28
    }
  ],
  "totalCount": 5,
  "page": 1
}
```

---

#### **Yahoo DSP Response: CONVERSIONRULE Segments (Retargeting)**

```json
{
  "segments": [
    {
      "id": 98774,
      "name": "Honda.com - CR-V Page Visitors",
      "segmentType": "CONVERSIONRULE",
      "status": "ACTIVE",
      "reach": 450000,
      "description": "Users who visited CR-V pages on Honda.com in last 30 days",
      "recency": "30_DAYS",
      "cpmLift": 0.0
    },
    {
      "id": 98775,
      "name": "Honda.com - Build & Price Abandoners",
      "segmentType": "CONVERSIONRULE",
      "status": "ACTIVE",
      "reach": 180000,
      "description": "Users who started but didn't complete build & price",
      "recency": "14_DAYS",
      "cpmLift": 0.0
    }
  ],
  "totalCount": 8,
  "page": 1
}
```

---

**Newton's Discovery Summary:**
```
DISCOVERED SEGMENTS (9 candidates across 4 types):

INTEREST (Yahoo Behavioral):
├── Auto Intenders SUV/Crossover (8.5M reach)
├── Auto Enthusiasts New Vehicle (12M reach)
└── Family Vehicle Shoppers (6.2M reach)

FACT (Third-Party Data):
├── Competitive Auto Toyota/Subaru (3.2M reach) - Oracle
├── In-Market Auto Near Purchase (2.1M reach) - Polk/IHS
└── SUV/Crossover Intenders Premium (4.8M reach) - Experian

LOOKALIKE:
├── Honda Website Converters LAL (5.1M reach)
└── Honda Dealer Visitors LAL (3.8M reach)

CONVERSIONRULE (Retargeting):
├── CR-V Page Visitors (450K reach)
└── Build & Price Abandoners (180K reach)

Now I need to evaluate these segments to determine optimal allocation...
```

---

### **Act 3: Segment Evaluation**

Newton uses Yahoo DSP's `Get_analytics_for_audiences_segment` to evaluate segment quality.

```python
# Evaluate top candidate segments
mcp_yahoo.Get_analytics_for_audiences_segment(
    segmentIds="98765,98766,98767,98768,98772,98774,98775"
)
```

---

#### **Yahoo DSP Response: Segment Analytics**

```json
{
  "segmentAnalytics": [
    {
      "segmentId": 98765,
      "name": "Auto Intenders - SUV/Crossover",
      "segmentType": "INTEREST",
      "reach": 8500000,
      "avgCPM": 6.50,
      "historicalCTR": 0.0012,
      "viewabilityRate": 0.71,
      "frequencyCapRecommendation": 4,
      "overlapAnalysis": {
        "98766": 0.35,
        "98767": 0.22,
        "98768": 0.45,
        "98772": 0.38
      },
      "performanceIndex": 72,
      "recommendation": "SCALE - High reach, efficient CPM"
    },
    {
      "segmentId": 98766,
      "name": "Competitive Auto - Toyota/Subaru",
      "segmentType": "FACT",
      "provider": "Oracle Data Cloud",
      "reach": 3200000,
      "avgCPM": 8.20,
      "dataFee": 1.50,
      "effectiveCPM": 9.70,
      "historicalCTR": 0.0018,
      "viewabilityRate": 0.68,
      "conversionRate": 0.023,
      "dealerVisitRate": 0.0045,
      "performanceIndex": 85,
      "recommendation": "CONQUEST - High intent, competitive shoppers"
    },
    {
      "segmentId": 98767,
      "name": "Honda Website Converters - Lookalike",
      "segmentType": "LOOKALIKE",
      "reach": 5100000,
      "avgCPM": 7.00,
      "historicalCTR": 0.0021,
      "viewabilityRate": 0.73,
      "conversionRate": 0.031,
      "dealerVisitRate": 0.0062,
      "performanceIndex": 88,
      "recommendation": "CORE - High-quality lookalike, strong conversion"
    },
    {
      "segmentId": 98768,
      "name": "In-Market Auto - Near Purchase",
      "segmentType": "FACT",
      "provider": "Polk/IHS Markit",
      "reach": 2100000,
      "avgCPM": 12.50,
      "dataFee": 2.50,
      "effectiveCPM": 15.00,
      "historicalCTR": 0.0028,
      "viewabilityRate": 0.75,
      "conversionRate": 0.048,
      "dealerVisitRate": 0.0095,
      "performanceIndex": 94,
      "recommendation": "CONVERSION - Highest intent, justify premium CPM"
    },
    {
      "segmentId": 98772,
      "name": "SUV/Crossover Intenders - Premium",
      "segmentType": "FACT",
      "provider": "Experian",
      "reach": 4800000,
      "avgCPM": 8.00,
      "dataFee": 2.00,
      "effectiveCPM": 10.00,
      "historicalCTR": 0.0015,
      "viewabilityRate": 0.70,
      "conversionRate": 0.028,
      "dealerVisitRate": 0.0052,
      "performanceIndex": 81,
      "recommendation": "CONSIDERATION - Good balance of reach and quality"
    },
    {
      "segmentId": 98774,
      "name": "Honda.com - CR-V Page Visitors",
      "segmentType": "CONVERSIONRULE",
      "reach": 450000,
      "avgCPM": 5.00,
      "historicalCTR": 0.0045,
      "viewabilityRate": 0.78,
      "conversionRate": 0.082,
      "dealerVisitRate": 0.018,
      "performanceIndex": 96,
      "recommendation": "RETARGETING - Highest conversion, limited scale"
    },
    {
      "segmentId": 98775,
      "name": "Honda.com - Build & Price Abandoners",
      "segmentType": "CONVERSIONRULE",
      "reach": 180000,
      "avgCPM": 5.00,
      "historicalCTR": 0.0062,
      "viewabilityRate": 0.80,
      "conversionRate": 0.125,
      "dealerVisitRate": 0.028,
      "performanceIndex": 98,
      "recommendation": "RETARGETING - Highest intent, must include"
    }
  ]
}
```

---

### **Newton's Segment Analysis & Selection**

```markdown
# SEGMENT EVALUATION MATRIX

| Segment | Type | Reach | Eff. CPM | CTR | Conv% | Dealer Visit | Score | Role |
|---------|------|-------|----------|-----|-------|--------------|-------|------|
| Auto Intenders SUV | INTEREST | 8.5M | $6.50 | 0.12% | - | - | 72 | SCALE |
| Competitive Toyota/Subaru | FACT | 3.2M | $9.70 | 0.18% | 2.3% | 0.45% | 85 | CONQUEST |
| Honda LAL Converters | LOOKALIKE | 5.1M | $7.00 | 0.21% | 3.1% | 0.62% | 88 | CORE |
| In-Market Near Purchase | FACT | 2.1M | $15.00 | 0.28% | 4.8% | 0.95% | 94 | CONVERSION |
| SUV Intenders Premium | FACT | 4.8M | $10.00 | 0.15% | 2.8% | 0.52% | 81 | CONSIDERATION |
| CR-V Page Visitors | RETARGET | 450K | $5.00 | 0.45% | 8.2% | 1.8% | 96 | RETARGET |
| Build & Price Abandoners | RETARGET | 180K | $5.00 | 0.62% | 12.5% | 2.8% | 98 | RETARGET |

# OVERLAP ANALYSIS

Key insight: 35% overlap between Auto Intenders SUV and Competitive Auto segments.
Recommendation: Use exclusions to avoid paying twice for same users.

# FUNNEL-BASED ALLOCATION

Given Honda's objectives (awareness + dealer visits), I'll allocate across the funnel:

## AWARENESS TIER (35% = $175K)
Purpose: Maximize unique reach among SUV intenders
Segments: Auto Intenders SUV/Crossover (8.5M reach)
Expected: 26.9M impressions, 32K clicks
Strategy: Broad reach, frequency cap at 4/week

## CONSIDERATION TIER (25% = $125K)  
Purpose: Engage high-quality intenders with proven intent signals
Segments: 
  - SUV/Crossover Intenders Premium (4.8M reach)
  - Honda LAL Converters (5.1M reach)
Expected: 13.9M impressions, 24K clicks
Strategy: Balanced reach/quality, frequency cap at 3/week

## CONQUEST TIER (20% = $100K)
Purpose: Win competitive shoppers considering Toyota/Subaru
Segments: Competitive Auto Toyota/Subaru (3.2M reach)
Expected: 10.3M impressions, 18.5K clicks
Strategy: Aggressive messaging, frequency cap at 5/week

## CONVERSION TIER (15% = $75K)
Purpose: Capture users closest to purchase decision
Segments: In-Market Auto Near Purchase (2.1M reach)
Expected: 5M impressions, 14K clicks
Strategy: Strong CTA, dealer locator, frequency cap at 6/week

## RETARGETING TIER (5% = $25K)
Purpose: Re-engage Honda.com visitors with highest intent
Segments:
  - CR-V Page Visitors (450K reach)
  - Build & Price Abandoners (180K reach)
Expected: 5M impressions, 25K clicks
Strategy: Sequential messaging, high frequency (10/week)

# TOTAL CAMPAIGN PROJECTIONS

Budget: $500,000
Duration: 90 days (Q1 2026)
Total Impressions: ~61M
Unique Reach: ~15M users
Avg Frequency: 4.1
Expected Clicks: 113K (0.19% avg CTR)
Expected Conversions: 2,850 (2.5% avg conv rate)
Expected Dealer Visits: 5,700 (0.94% dealer visit rate)

Blended CPM: $8.20
Cost Per Click: $4.42
Cost Per Conversion: $175
Cost Per Dealer Visit: $88
```

---

### **Act 4: Campaign Execution**

Newton executes the buy using standard AdCP tools with selected segments.

```python
# Step 1: Sync Creatives
mcp_yahoo.sync_creatives(
    creatives=[
        {
            "creative_id": "honda_crv_spring_2026_300x250_awareness",
            "name": "Honda CR-V - Adventure Awaits (Awareness)",
            "format_id": "display_300x250",
            "click_through_url": "https://automobiles.honda.com/cr-v",
            "preview_url": "https://cdn.honda.com/ads/crv_spring_awareness.jpg",
            "assets": {
                "image": {
                    "url": "https://cdn.honda.com/ads/crv_spring_awareness.jpg",
                    "width": 300,
                    "height": 250
                }
            }
        },
        {
            "creative_id": "honda_crv_spring_2026_300x250_conquest",
            "name": "Honda CR-V - Compare & Win (Conquest)",
            "format_id": "display_300x250",
            "click_through_url": "https://automobiles.honda.com/cr-v/compare",
            "preview_url": "https://cdn.honda.com/ads/crv_spring_conquest.jpg"
        },
        {
            "creative_id": "honda_crv_spring_2026_300x250_dealer",
            "name": "Honda CR-V - Find Your Dealer (Conversion)",
            "format_id": "display_300x250",
            "click_through_url": "https://automobiles.honda.com/tools/dealer-locator",
            "preview_url": "https://cdn.honda.com/ads/crv_spring_dealer.jpg"
        },
        {
            "creative_id": "honda_crv_spring_2026_300x250_retarget",
            "name": "Honda CR-V - Complete Your Build (Retargeting)",
            "format_id": "display_300x250",
            "click_through_url": "https://automobiles.honda.com/cr-v/build",
            "preview_url": "https://cdn.honda.com/ads/crv_spring_retarget.jpg"
        }
    ]
)
```

```python
# Step 2: Create Media Buy with Funnel-Based Allocation
mcp_yahoo.create_media_buy(
    buyer_ref="honda_crv_yahoo_dsp_q1_2026",
    brand_manifest={
        "name": "Honda",
        "url": "https://honda.com",
        "industry": "automotive"
    },
    start_time="2026-01-01T00:00:00Z",
    end_time="2026-03-31T23:59:59Z",
    packages=[
        # AWARENESS TIER (35% = $175K)
        {
            "package_id": "awareness_auto_intenders",
            "product_id": "yahoo_display_300x250",
            "budget": 175000,
            "impressions": 26900000,
            "creative_ids": ["honda_crv_spring_2026_300x250_awareness"],
            "pacing": "even",
            "targeting_overlay": {
                "segment_ids": [98765],  # Auto Intenders SUV/Crossover
                "geo_country_any_of": ["US"],
                "frequency_cap": {
                    "limit": 4,
                    "duration": 7,
                    "duration_unit": "DAY"
                }
            }
        },
        # CONSIDERATION TIER (25% = $125K)
        {
            "package_id": "consideration_premium_intenders",
            "product_id": "yahoo_display_300x250",
            "budget": 125000,
            "impressions": 13900000,
            "creative_ids": ["honda_crv_spring_2026_300x250_awareness"],
            "pacing": "even",
            "targeting_overlay": {
                "segment_ids": [98772, 98767],  # SUV Premium + Honda LAL
                "segment_exclusions": [98765],  # Exclude awareness tier
                "geo_country_any_of": ["US"],
                "frequency_cap": {
                    "limit": 3,
                    "duration": 7,
                    "duration_unit": "DAY"
                }
            }
        },
        # CONQUEST TIER (20% = $100K)
        {
            "package_id": "conquest_competitive_auto",
            "product_id": "yahoo_display_300x250",
            "budget": 100000,
            "impressions": 10300000,
            "creative_ids": ["honda_crv_spring_2026_300x250_conquest"],
            "pacing": "even",
            "targeting_overlay": {
                "segment_ids": [98766],  # Competitive Toyota/Subaru
                "segment_exclusions": [98765, 98772, 98767],  # Exclude other tiers
                "geo_country_any_of": ["US"],
                "frequency_cap": {
                    "limit": 5,
                    "duration": 7,
                    "duration_unit": "DAY"
                }
            }
        },
        # CONVERSION TIER (15% = $75K)
        {
            "package_id": "conversion_inmarket",
            "product_id": "yahoo_display_300x250",
            "budget": 75000,
            "impressions": 5000000,
            "creative_ids": ["honda_crv_spring_2026_300x250_dealer"],
            "pacing": "even",
            "targeting_overlay": {
                "segment_ids": [98768],  # In-Market Near Purchase
                "segment_exclusions": [98774, 98775],  # Exclude retargeting
                "geo_country_any_of": ["US"],
                "frequency_cap": {
                    "limit": 6,
                    "duration": 7,
                    "duration_unit": "DAY"
                }
            }
        },
        # RETARGETING TIER (5% = $25K)
        {
            "package_id": "retargeting_honda_visitors",
            "product_id": "yahoo_display_300x250",
            "budget": 25000,
            "impressions": 5000000,
            "creative_ids": ["honda_crv_spring_2026_300x250_retarget"],
            "pacing": "even",
            "targeting_overlay": {
                "segment_ids": [98774, 98775],  # CR-V Visitors + Abandoners
                "geo_country_any_of": ["US"],
                "frequency_cap": {
                    "limit": 10,
                    "duration": 7,
                    "duration_unit": "DAY"
                }
            }
        }
    ]
)
```

---

#### **Yahoo DSP Response: Campaign Created**

```json
{
  "status": "pending",
  "media_buy_id": "honda_crv_yahoo_dsp_q1_2026",
  "external_ids": {
    "yahoo_campaign_id": "honda_crv_yahoo_dsp_q1_2026",
    "yahoo_order_id": 789012
  },
  
  "packages": [
    {
      "package_id": "awareness_auto_intenders",
      "status": "pending",
      "external_id": "2345678",
      "line": {
        "id": 2345678,
        "name": "Honda CR-V Q1 2026 - Awareness",
        "status": "PENDING_REVIEW",
        "scheduleBudget": 175000,
        "dailyBudget": 1944.44,
        "segmentIds": [98765],
        "estimatedReach": 6800000,
        "estimatedImpressions": 26900000,
        "estimatedFrequency": 3.96
      }
    },
    {
      "package_id": "consideration_premium_intenders",
      "status": "pending",
      "external_id": "2345679",
      "line": {
        "id": 2345679,
        "name": "Honda CR-V Q1 2026 - Consideration",
        "status": "PENDING_REVIEW",
        "scheduleBudget": 125000,
        "dailyBudget": 1388.89,
        "segmentIds": [98772, 98767],
        "estimatedReach": 4200000,
        "estimatedImpressions": 13900000,
        "estimatedFrequency": 3.31
      }
    },
    {
      "package_id": "conquest_competitive_auto",
      "status": "pending",
      "external_id": "2345680",
      "line": {
        "id": 2345680,
        "name": "Honda CR-V Q1 2026 - Conquest",
        "status": "PENDING_REVIEW",
        "scheduleBudget": 100000,
        "dailyBudget": 1111.11,
        "segmentIds": [98766],
        "estimatedReach": 2400000,
        "estimatedImpressions": 10300000,
        "estimatedFrequency": 4.29
      }
    },
    {
      "package_id": "conversion_inmarket",
      "status": "pending",
      "external_id": "2345681",
      "line": {
        "id": 2345681,
        "name": "Honda CR-V Q1 2026 - Conversion",
        "status": "PENDING_REVIEW",
        "scheduleBudget": 75000,
        "dailyBudget": 833.33,
        "segmentIds": [98768],
        "estimatedReach": 1500000,
        "estimatedImpressions": 5000000,
        "estimatedFrequency": 3.33
      }
    },
    {
      "package_id": "retargeting_honda_visitors",
      "status": "pending",
      "external_id": "2345682",
      "line": {
        "id": 2345682,
        "name": "Honda CR-V Q1 2026 - Retargeting",
        "status": "PENDING_REVIEW",
        "scheduleBudget": 25000,
        "dailyBudget": 277.78,
        "segmentIds": [98774, 98775],
        "estimatedReach": 520000,
        "estimatedImpressions": 5000000,
        "estimatedFrequency": 9.62
      }
    }
  ],
  
  "campaignSummary": {
    "totalBudget": 500000,
    "totalEstimatedImpressions": 61100000,
    "totalEstimatedReach": 15420000,
    "averageFrequency": 3.96,
    "blendedCPM": 8.18,
    "segmentsUsed": 7,
    "creativesAssigned": 4
  },
  
  "biddingConfig": {
    "bidStrategy": "AUTOBID",
    "goalType": "CLICK",
    "pacingType": "EVEN",
    "learningPhase": {
      "enabled": true,
      "durationDays": 7,
      "status": "NOT_STARTED"
    }
  },
  
  "audienceOverlapMitigation": {
    "strategy": "EXCLUSIONS",
    "exclusionsApplied": 4,
    "estimatedDuplicateReduction": "18%"
  }
}
```

---

**Newton's Execution Summary:**

```
CAMPAIGN BOOKED: Honda CR-V Q1 2026 - Yahoo DSP

✅ ALLOCATION EXECUTED:
   Total Budget: $500,000
   Platform: Yahoo DSP
   Flight: Jan 1 - Mar 31, 2026 (90 days)

✅ SEGMENTS ACTIVATED (7 segments across funnel):
   
   AWARENESS (35%): Auto Intenders SUV/Crossover
   ├── Budget: $175K
   ├── Reach: 6.8M users
   └── Impressions: 26.9M
   
   CONSIDERATION (25%): SUV Premium + Honda LAL
   ├── Budget: $125K
   ├── Reach: 4.2M users
   └── Impressions: 13.9M
   
   CONQUEST (20%): Competitive Toyota/Subaru
   ├── Budget: $100K
   ├── Reach: 2.4M users
   └── Impressions: 10.3M
   
   CONVERSION (15%): In-Market Near Purchase
   ├── Budget: $75K
   ├── Reach: 1.5M users
   └── Impressions: 5.0M
   
   RETARGETING (5%): Honda.com Visitors + Abandoners
   ├── Budget: $25K
   ├── Reach: 520K users
   └── Impressions: 5.0M

✅ CAMPAIGN PROJECTIONS:
   Total Reach: 15.4M unique users
   Total Impressions: 61.1M
   Avg Frequency: 4.0
   Blended CPM: $8.18
   
✅ OPTIMIZATION:
   Audience overlap exclusions applied (18% duplicate reduction)
   AUTOBID enabled with 7-day learning phase
   Frequency caps set per tier

Campaign pending review. Expected approval within 24 hours.
```

---

### **Act 5: Performance Monitoring (Week 4)**

Newton checks performance after 4 weeks to validate segment selection and funnel strategy.

```python
mcp_yahoo.get_media_buy_delivery(
    media_buy_ids=["honda_crv_yahoo_dsp_q1_2026"],
    start_date="2026-01-01",
    end_date="2026-01-28"
)
```

---

#### **Yahoo DSP Performance Report**

```json
{
  "packages": [
    {
      "package_id": "awareness_auto_intenders",
      "external_id": "2345678",
      "status": "delivering",
      "impressions": 9200000,
      "clicks": 11040,
      "spend": 59800.00,
      "metadata": {
        "lineId": 2345678,
        "lineName": "Honda CR-V Q1 2026 - Awareness",
        "lineStatus": "ACTIVE",
        "segmentId": 98765,
        "segmentName": "Auto Intenders - SUV/Crossover",
        "ctr": 0.0012,
        "cpm": 6.50,
        "viewabilityRate": 0.72,
        "uniqueUsers": 2350000,
        "frequency": 3.91,
        "budgetUtilization": 0.342
      }
    },
    {
      "package_id": "consideration_premium_intenders",
      "external_id": "2345679",
      "status": "delivering",
      "impressions": 4650000,
      "clicks": 7440,
      "spend": 42750.00,
      "metadata": {
        "lineId": 2345679,
        "lineName": "Honda CR-V Q1 2026 - Consideration",
        "lineStatus": "ACTIVE",
        "segmentIds": [98772, 98767],
        "ctr": 0.0016,
        "cpm": 9.19,
        "viewabilityRate": 0.71,
        "uniqueUsers": 1420000,
        "frequency": 3.27,
        "conversions": 130,
        "conversionRate": 0.0175,
        "budgetUtilization": 0.342
      }
    },
    {
      "package_id": "conquest_competitive_auto",
      "external_id": "2345680",
      "status": "delivering",
      "impressions": 3500000,
      "clicks": 6650,
      "spend": 33950.00,
      "metadata": {
        "lineId": 2345680,
        "lineName": "Honda CR-V Q1 2026 - Conquest",
        "lineStatus": "ACTIVE",
        "segmentId": 98766,
        "segmentName": "Competitive Auto - Toyota/Subaru",
        "ctr": 0.0019,
        "cpm": 9.70,
        "viewabilityRate": 0.69,
        "uniqueUsers": 820000,
        "frequency": 4.27,
        "conversions": 155,
        "conversionRate": 0.0233,
        "dealerVisits": 310,
        "dealerVisitRate": 0.0047,
        "budgetUtilization": 0.340
      }
    },
    {
      "package_id": "conversion_inmarket",
      "external_id": "2345681",
      "status": "delivering",
      "impressions": 1680000,
      "clicks": 4704,
      "spend": 25200.00,
      "metadata": {
        "lineId": 2345681,
        "lineName": "Honda CR-V Q1 2026 - Conversion",
        "lineStatus": "ACTIVE",
        "segmentId": 98768,
        "segmentName": "In-Market Auto - Near Purchase",
        "ctr": 0.0028,
        "cpm": 15.00,
        "viewabilityRate": 0.76,
        "uniqueUsers": 510000,
        "frequency": 3.29,
        "conversions": 220,
        "conversionRate": 0.0468,
        "dealerVisits": 485,
        "dealerVisitRate": 0.0103,
        "budgetUtilization": 0.336
      }
    },
    {
      "package_id": "retargeting_honda_visitors",
      "external_id": "2345682",
      "status": "delivering",
      "impressions": 1650000,
      "clicks": 7425,
      "spend": 8250.00,
      "metadata": {
        "lineId": 2345682,
        "lineName": "Honda CR-V Q1 2026 - Retargeting",
        "lineStatus": "ACTIVE",
        "segmentIds": [98774, 98775],
        "ctr": 0.0045,
        "cpm": 5.00,
        "viewabilityRate": 0.79,
        "uniqueUsers": 175000,
        "frequency": 9.43,
        "conversions": 410,
        "conversionRate": 0.0552,
        "dealerVisits": 248,
        "dealerVisitRate": 0.0033,
        "budgetUtilization": 0.330
      }
    }
  ],
  
  "totals": {
    "impressions": 20680000,
    "clicks": 37259,
    "spend": 169950.00,
    "conversions": 915,
    "dealerVisits": 1043
  },
  
  "campaignMetrics": {
    "blendedCPM": 8.22,
    "blendedCTR": 0.0018,
    "blendedConversionRate": 0.0245,
    "costPerClick": 4.56,
    "costPerConversion": 185.74,
    "costPerDealerVisit": 163.04,
    "uniqueReach": 5275000,
    "avgFrequency": 3.92,
    "budgetUtilization": 0.340,
    "paceStatus": "ON_TRACK"
  }
}
```

---

### **Newton's Performance Analysis**

```markdown
# Honda CR-V Q1 2026 - Yahoo DSP Campaign Analysis (Week 4)

## Campaign Overview
- Platform: Yahoo DSP
- Budget: $500,000 (allocated by MMM)
- Spend to date: $169,950 (34% of budget)
- Duration: 28 days of 90 (31% elapsed)
- Status: ON TRACK ✅

## Funnel Performance Analysis

### By Tier Performance:

| Tier | Budget | Spend | Imps | CTR | Conv | Conv% | Dealer Visits | DVR |
|------|--------|-------|------|-----|------|-------|---------------|-----|
| Awareness | $175K | $59.8K | 9.2M | 0.12% | - | - | - | - |
| Consideration | $125K | $42.8K | 4.7M | 0.16% | 130 | 1.75% | - | - |
| Conquest | $100K | $34.0K | 3.5M | 0.19% | 155 | 2.33% | 310 | 0.47% |
| Conversion | $75K | $25.2K | 1.7M | 0.28% | 220 | 4.68% | 485 | 1.03% |
| Retargeting | $25K | $8.3K | 1.7M | 0.45% | 410 | 5.52% | 248 | 0.33% |

### KEY INSIGHTS:

1. **RETARGETING OUTPERFORMING** 🌟
   - Highest CTR (0.45%) and conversion rate (5.52%)
   - Only 5% of budget but driving 45% of conversions
   - Consider increasing allocation in optimization

2. **IN-MARKET SEGMENT VALIDATES PREMIUM CPM**
   - $15 CPM (highest) but 1.03% dealer visit rate (highest)
   - Cost per dealer visit: $52 (EXCELLENT)
   - Polk/IHS Markit data proving valuable

3. **CONQUEST STRATEGY WORKING**
   - Competitive Toyota/Subaru shoppers converting at 2.33%
   - 310 dealer visits from competitive considerers
   - Winning share from competition

4. **AWARENESS TIER EFFICIENT**
   - $6.50 CPM delivering scale
   - 2.35M unique users reached
   - Setting up lower funnel success

## Segment-Level Performance

### TOP PERFORMING SEGMENTS:

1. **Build & Price Abandoners** (Retargeting)
   - Conversion Rate: 12.5%
   - Dealer Visit Rate: 2.8%
   - STATUS: ⭐ STAR PERFORMER

2. **In-Market Near Purchase** (Polk/IHS)
   - Conversion Rate: 4.68%
   - Dealer Visit Rate: 1.03%
   - STATUS: ⭐ HIGH INTENT VALIDATED

3. **Honda Website Converters LAL**
   - Conversion Rate: 3.1%
   - Dealer Visit Rate: 0.62%
   - STATUS: ✅ CORE PERFORMER

4. **Competitive Auto Toyota/Subaru**
   - Conversion Rate: 2.33%
   - Dealer Visit Rate: 0.47%
   - STATUS: ✅ CONQUEST WORKING

## ROI Analysis

### Conversions (Form Fills, Quote Requests):
- Total Conversions: 915
- Cost Per Conversion: $185.74
- Projected Full Campaign: 2,690 conversions

### Dealer Visits (Measured via Yahoo + Honda):
- Total Dealer Visits: 1,043
- Cost Per Dealer Visit: $163.04
- Projected Full Campaign: 3,067 dealer visits

### Assuming 5% dealer visit to sale conversion:
- Estimated Sales: 52 vehicles (month 1)
- Projected Campaign Sales: 153 vehicles
- At $35K avg vehicle price: $5.36M revenue
- Campaign ROAS: 10.7X ($5.36M / $500K)

## Optimization Recommendations

### 1. INCREASE RETARGETING BUDGET ✅ RECOMMENDED
Current: 5% ($25K) → Proposed: 10% ($50K)
Rationale: Highest conversion rate (5.52%), efficient CPM ($5.00)
Expected Impact: +400 additional conversions

### 2. EXPAND IN-MARKET SEGMENT
Consider adding:
- In-Market Auto - 60 day window (broader reach)
- Dealer Lot Visitors (geo-targeting)
Expected Impact: +25% conversion volume

### 3. TEST SEQUENTIAL MESSAGING
Move awareness converters to consideration creative
Move consideration converters to dealer-focused creative
Expected Impact: +15% funnel efficiency

### 4. REDUCE AWARENESS ALLOCATION
Current: 35% → Proposed: 30%
Shift 5% to retargeting
Rationale: Awareness tier at efficient reach, lower funnel needs scale

## Next Steps

1. ✅ Continue current strategy through week 6 (learning phase complete)
2. 📊 Request mid-campaign optimization call with Yahoo DSP
3. 🎯 Prepare retargeting budget increase proposal
4. 📈 Generate dealer visit attribution report
```

---

## 🎭 Demo Flow Summary

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           HONDA + YAHOO DSP DEMO SEQUENCE                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                │
│   AGENCY/MMM           NEWTON                    YAHOO DSP                                    │
│      │                    │                          │                                         │
│      │ ① Strategic Brief  │                          │                                         │
│      │   $500K to Yahoo   │                          │                                         │
│      │   Auto intenders   │                          │                                         │
│      │ ─────────────────> │                          │                                         │
│      │                    │                          │                                         │
│      │                    │ ② getAudienceSegments()  │                                         │
│      │                    │    (INTEREST, FACT,      │                                         │
│      │                    │     LOOKALIKE, CONVERSIONRULE)                                     │
│      │                    │ ────────────────────────>│                                         │
│      │                    │                          │                                         │
│      │                    │ ③ 9 segments discovered  │                                         │
│      │                    │ <────────────────────────│                                         │
│      │                    │                          │                                         │
│      │                    │ ④ Get_analytics_for_     │                                         │
│      │                    │    audiences_segment()   │                                         │
│      │                    │ ────────────────────────>│                                         │
│      │                    │                          │                                         │
│      │                    │ ⑤ Segment analytics      │                                         │
│      │                    │    (reach, CPM, conv%)   │                                         │
│      │                    │ <────────────────────────│                                         │
│      │                    │                          │                                         │
│      │               ┌────┴────┐                     │                                         │
│      │               │ SELECT  │                     │                                         │
│      │               │SEGMENTS │                     │                                         │
│      │               │ Funnel  │                     │                                         │
│      │               │ based   │                     │                                         │
│      │               └────┬────┘                     │                                         │
│      │                    │                          │                                         │
│      │                    │ ⑥ sync_creatives()       │                                         │
│      │                    │ ────────────────────────>│                                         │
│      │                    │                          │                                         │
│      │                    │ ⑦ create_media_buy()     │                                         │
│      │                    │    (5 packages/tiers)    │                                         │
│      │                    │ ────────────────────────>│                                         │
│      │                    │                          │                                         │
│      │                    │ ⑧ Campaign created       │                                         │
│      │                    │    61M imps, 15M reach   │                                         │
│      │                    │ <────────────────────────│                                         │
│      │                    │                          │                                         │
│      │ ⑨ CONFIRMATION    │                          │                                         │
│      │   5 tiers active  │                          │                                         │
│      │ <───────────────── │                          │                                         │
│      │                    │                          │                                         │
│      │  ═══════════════════════  WEEK 4  ═══════════════════════════                          │
│      │                    │                          │                                         │
│      │                    │ ⑩ get_media_buy_delivery()                                        │
│      │                    │ ────────────────────────>│                                         │
│      │                    │                          │                                         │
│      │                    │ ⑪ Performance report     │                                         │
│      │                    │    915 conv, 1043 visits │                                         │
│      │                    │ <────────────────────────│                                         │
│      │                    │                          │                                         │
│      │ ⑫ ANALYSIS        │                          │                                         │
│      │   10.7X ROAS      │                          │                                         │
│      │   Optimization    │                          │                                         │
│      │   recommendations │                          │                                         │
│      │ <───────────────── │                          │                                         │
│      │                    │                          │                                         │
│      ▼                    ▼                          ▼                                         │
│                                                                                                │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Demo Talking Points

### **For Audience:**

1. **"Newton operationalizes strategic decisions"**
   - MMM determines allocation ($500K to Yahoo DSP)
   - Audience modeling defines target (auto intenders 25-54)
   - Newton executes using native DSP tools

2. **"Newton uses REAL Yahoo DSP tools"**
   - `getAudienceSegments` - Discovers 9 segments across 4 types
   - `Get_analytics_for_audiences_segment` - Evaluates reach, CPM, conversion rates
   - Not simulated - actual Yahoo DSP API integration

3. **"Intelligent segment selection"**
   - Newton evaluates segments on multiple dimensions
   - Allocates budget by funnel stage (awareness → retargeting)
   - Applies overlap exclusions to avoid waste (18% duplicate reduction)

4. **"Funnel-based strategy proves out"**
   - Retargeting: 5% budget → 45% of conversions
   - In-Market: Highest CPM ($15) but best dealer visit rate (1.03%)
   - Premium data (Polk/IHS) justifies premium price

5. **"Measurable business outcomes"**
   - 915 conversions at $185 CPA
   - 1,043 dealer visits at $163 cost
   - Projected 10.7X ROAS ($5.36M revenue on $500K spend)

---

## 🚀 Running the Demo

### **Setup (Before Demo):**

1. Ensure Yahoo DSP service is running:
   ```bash
   aws ecs describe-services --cluster salesagent-yahoo --services salesagent-yahoo --region us-east-1
   ```

2. Verify Newton has MCP server registered:
   - `mcp_yahoo` → `http://yahoo.salesagent.local:9580/mcp`

3. Confirm Honda advertiser ID is configured (accountId: 12345)

### **Demo Execution:**

Run Newton with the scenario prompt:

```
PROMPT: "Honda has allocated $500K to Yahoo DSP for their CR-V Spring Launch 
campaign (Q1 2026). This allocation came from their Media Mix Model.

The audience modeling team identified the target: Auto intenders considering 
SUVs, age 25-54, with a focus on competitive conquesting (Toyota RAV4, 
Subaru Outback considerers).

Your job is to:
1. Discover available audience segments on Yahoo DSP
2. Evaluate segment quality and fit
3. Select the optimal segment mix for a funnel-based strategy
4. Execute the $500K buy across awareness, consideration, conquest, 
   conversion, and retargeting tiers
5. After 4 weeks, analyze performance and recommend optimizations"
```

Newton will:
1. Call `getAudienceSegments` (4 segment types: INTEREST, FACT, LOOKALIKE, CONVERSIONRULE)
2. Call `Get_analytics_for_audiences_segment` to evaluate candidates
3. Analyze and select optimal segments by funnel stage
4. Execute `sync_creatives` + `create_media_buy` with 5 packages
5. Call `get_media_buy_delivery` after simulated 4 weeks
6. Analyze funnel performance and calculate ROAS
7. Recommend optimizations (increase retargeting, expand in-market)

---

## 📊 Expected Demo Outcomes

### **Audience Takeaways:**

1. ✅ **Newton works with native DSP tools**
   - Not just AdCP abstractions
   - Uses actual Yahoo DSP audience discovery APIs
   - Evaluates real segment analytics

2. ✅ **Strategic execution, not just order-taking**
   - Receives allocation from MMM (strategy)
   - Makes intelligent segment selection decisions (tactics)
   - Allocates budget by funnel stage (execution)

3. ✅ **Data-driven optimization**
   - Segment analytics inform selection
   - Overlap exclusions reduce waste (18%)
   - Performance data drives recommendations

4. ✅ **Measurable business outcomes**
   - Dealer visits tracked (1,043)
   - ROAS calculated (10.7X)
   - Clear path to vehicle sales

5. ✅ **Funnel strategy validated**
   - Retargeting: Smallest budget, biggest impact
   - Premium data: Higher CPM justified by results
   - Full-funnel approach > single-tier buying

---

## 📝 Demo Notes

**Preparation time:** 5 minutes  
**Demo duration:** 15-20 minutes (live)  
**Technical level:** Medium-High (assumes DSP/audience knowledge)

**Key moments to emphasize:**
1. Newton calling `getAudienceSegments` with different segment types
2. Segment analytics comparison (reach vs CPM vs conversion rate)
3. Funnel-based budget allocation logic
4. Overlap exclusion strategy (18% waste reduction)
5. Week 4 performance: Retargeting outperformance
6. ROAS calculation: 10.7X ($5.36M on $500K)

**Native Yahoo tools highlighted:**
- `getAudienceSegments` - 4 segment types (INTEREST, FACT, LOOKALIKE, CONVERSIONRULE)
- `Get_analytics_for_audiences_segment` - Reach, CPM, CTR, conversion rate, overlap

**Backup plan:** Pre-recorded responses if live demo fails

---

## 🔗 Related Demos

This demo complements the **NBCU/FreeWheel Linear + Streaming Demo**:

| Aspect | Yahoo DSP Demo | NBCU Demo |
|--------|----------------|-----------|
| Channel | Programmatic Display | Linear TV + Streaming |
| Targeting | Audience segments | Programming/Daypart |
| Pricing | Auction (CPM) | Guaranteed (Unit rate) |
| Native Tools | `getAudienceSegments` | `get_products` |
| Measurement | Conversions, Dealer Visits | GRPs, Impressions |

**Together they show:** Newton can orchestrate cross-channel campaigns using native tools from each platform while maintaining strategic coherence.

---

This demo powerfully demonstrates Newton using **real Yahoo DSP tools** to operationalize strategic media decisions! 🚗🚀
