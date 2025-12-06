# Newton + Yahoo DSP Demo Script (CTV Streaming)

## 🎯 Demo Objective

Show Newton executing a **CTV streaming campaign** on **Yahoo DSP** using **pre-negotiated publisher deals**, demonstrating:

1. **Agency workflow** - Newton discovers pre-negotiated deals with CTV publishers
2. **Deal-based buying** - Using Yahoo DSP's `/traffic/deals` API
3. **Multi-publisher execution** - Activating buys across 12 streaming publishers
4. **Native DSP tools** - Yahoo-specific tools alongside standard AdCP

---

## 📋 Demo Scenario

**Advertiser:** Honda  
**Campaign:** CR-V CTV Q1 2026  
**Budget:** $2M allocated to CTV streaming (agency-negotiated deals)

**Publishers with Pre-Negotiated Deals:**
| Publisher | Deal Type | Est. CPM | Inventory |
|-----------|-----------|----------|-----------|
| Disney (DSE) | PG | $42 | Disney+, Hulu, ESPN+ |
| Paramount | PG | $38 | Paramount+, Pluto TV |
| Warner Bros. Discovery | PG | $40 | Max, Discovery+, TNT Sports |
| HBO Max | PG | $45 | HBO Max |
| Discovery+ | PG | $32 | Discovery+, Food Network, HGTV |
| Tubi | PMP | $22 floor | Tubi |
| Fox Sports | PMP | $35 floor | Fox Sports Live |
| Roku | PMP | $28 floor | Roku Channel |
| VEVO | PMP | $18 floor | VEVO Music Videos |
| Vizio | Preferred | $20 | WatchFree+ |
| Samsung | Preferred | $22 | Samsung TV+ |
| LG | Preferred | $20 | LG Channels |

**Newton's Task:**
- Discover available deals via Yahoo DSP
- Review deal terms and inventory
- Allocate budget across publishers
- Create campaign and lines targeting deals
- Sync CTV creatives
- Monitor delivery by publisher

---

## 🎬 Demo Script

### **Act 1: Strategic Brief**

Newton receives instructions from Honda's agency with CTV allocation.

```python
# Newton receives strategic brief:
brief = {
    "advertiser": "Honda",
    "campaign": "CR-V CTV Q1 2026",
    "budget": 2000000,
    "currency": "USD",
    "platform": "yahoo_dsp",
    "channel": "CTV",
    
    "context": {
        "description": "Agency has negotiated deals with 12 CTV publishers",
        "workflow": "Activate pre-negotiated deals via Yahoo DSP",
        "note": "Deals already loaded in DSP - Newton discovers and executes"
    },
    
    "objectives": {
        "primary": "reach",
        "secondary": "video_completion",
        "kpis": ["unique_reach", "video_completion_rate", "brand_lift"]
    },
    
    "creative": {
        "formats": ["15s", "30s"],
        "assets_ready": True,
        "approval_status": "approved"
    },
    
    "flight": {
        "start": "2026-01-01",
        "end": "2026-03-31"
    }
}
```

**Newton's Internal Reasoning:**
```
"Honda has $2M for CTV streaming. The agency already negotiated deals 
with major publishers. My job is to:

1. DISCOVER available deals in Yahoo DSP
2. REVIEW deal terms, pricing, and inventory
3. ALLOCATE budget across publishers strategically
4. CREATE campaign and lines targeting each deal
5. SYNC CTV video creatives
6. MONITOR delivery by publisher

Let me start by querying available deals..."
```

---

### **Act 2: Deal Discovery**

Newton uses Yahoo DSP's `listDeals` tool to discover available CTV deals.

```python
# Step 1: Query all active CTV deals
mcp_yahoo_dsp.listDeals(
    status="ACTIVE",
    media_type="CTV_VIDEO",
    limit=50
)
```

**Yahoo DSP Response:**
```json
{
  "deals": [
    {
      "deal_id": "DSE-HONDA-Q1-2026",
      "publisher": "Disney Streaming (DSE)",
      "deal_type": "PROGRAMMATIC_GUARANTEED",
      "media_type": "CTV_VIDEO",
      "cpm_rate": 42.00,
      "guaranteed_impressions": 5000000,
      "min_spend": 210000,
      "inventory": ["Disney+", "Hulu", "ESPN+"],
      "brand_safety_tier": "PREMIUM",
      "viewability_guarantee": 0.85,
      "status": "ACTIVE"
    },
    {
      "deal_id": "PARA-HONDA-Q1-2026",
      "publisher": "Paramount",
      "deal_type": "PROGRAMMATIC_GUARANTEED",
      "media_type": "CTV_VIDEO",
      "cpm_rate": 38.00,
      "guaranteed_impressions": 4000000,
      "inventory": ["Paramount+", "Pluto TV", "CBS Sports"],
      "status": "ACTIVE"
    },
    {
      "deal_id": "TUBI-HONDA-Q1-2026",
      "publisher": "Tubi",
      "deal_type": "PRIVATE_AUCTION",
      "media_type": "CTV_VIDEO",
      "floor_cpm": 22.00,
      "avg_win_cpm": 26.50,
      "available_impressions": 8000000,
      "estimated_win_rate": 0.65,
      "status": "ACTIVE"
    }
    // ... 9 more deals (WBD, HBO, Discovery+, Fox, Roku, VEVO, Vizio, Samsung, LG)
  ],
  "totalCount": 12,
  "summary": {
    "totalAvailableImpressions": 51000000,
    "totalBudgetAtRate": 1940000,
    "pgDeals": 5,
    "pmpDeals": 7
  }
}
```

**Newton's Analysis:**
```
"I've discovered 12 active CTV deals for Honda:

PREMIUM (Programmatic Guaranteed - fixed CPM):
- Disney: $42 CPM, 5M imps guaranteed → $210K
- Paramount: $38 CPM, 4M imps → $152K
- WBD: $40 CPM, 4M imps → $160K
- HBO Max: $45 CPM, 3M imps → $135K
- Discovery+: $32 CPM, 3M imps → $96K

AUCTION (Private Marketplace - floor CPM):
- Tubi: $22 floor, ~8M avail
- Fox Sports: $35 floor, ~4M avail
- Roku: $28 floor, ~6M avail
- VEVO: $18 floor, ~5M avail

OEM (Preferred Deals - fixed CPM):
- Vizio: $20 CPM, ~4M avail
- Samsung: $22 CPM, ~3M avail
- LG: $20 CPM, ~2M avail

Let me get detailed info on the Disney deal..."
```

---

### **Act 3: Deal Detail Review**

Newton digs deeper into specific deal terms.

```python
# Get detailed info on Disney deal
mcp_yahoo_dsp.getDealDetails(deal_id="DSE-HONDA-Q1-2026")
```

**Response:**
```json
{
  "deal_id": "DSE-HONDA-Q1-2026",
  "publisher": "Disney Streaming (DSE)",
  "deal_type": "PROGRAMMATIC_GUARANTEED",
  "media_type": "CTV_VIDEO",
  
  "pricing": {
    "type": "FIXED",
    "cpm_rate": 42.00,
    "guaranteed_impressions": 5000000,
    "min_spend": 210000,
    "currency": "USD"
  },
  
  "inventory": ["Disney+", "Hulu", "ESPN+"],
  "content_categories": ["Entertainment", "Sports", "Family"],
  
  "creative_specs": {
    "formats": ["15s", "30s", "60s"],
    "max_file_size_mb": 100,
    "aspect_ratios": ["16:9"],
    "audio_required": true
  },
  
  "targeting_available": {
    "geo": true,
    "daypart": true,
    "device": true,
    "content_rating": true,
    "genre": true
  },
  
  "brand_safety_tier": "PREMIUM",
  "viewability_guarantee": 0.85,
  
  "forecast": {
    "guaranteed_impressions": 5000000,
    "estimated_reach": 1428571,
    "estimated_frequency": 3.5,
    "confidence": 0.95
  }
}
```

---

### **Act 4: Budget Allocation Strategy**

Newton plans budget allocation across publishers.

```
NEWTON'S ALLOCATION STRATEGY:

Given $2M budget and available deals, I'll allocate as follows:

## PREMIUM TIER (65% = $1.3M)
Premium streaming with brand safety and viewability guarantees.

| Publisher | Deal ID | Budget | Est. Impressions |
|-----------|---------|--------|------------------|
| Disney | DSE-HONDA-Q1-2026 | $300K | 7.1M |
| Paramount | PARA-HONDA-Q1-2026 | $250K | 6.6M |
| WBD | WBD-HONDA-Q1-2026 | $280K | 7.0M |
| HBO Max | HBO-HONDA-Q1-2026 | $225K | 5.0M |
| Discovery+ | DISC-HONDA-Q1-2026 | $245K | 7.7M |

## SCALE TIER (25% = $500K)
High-reach AVOD/FAST with auction efficiency.

| Publisher | Deal ID | Budget | Est. Impressions |
|-----------|---------|--------|------------------|
| Tubi | TUBI-HONDA-Q1-2026 | $175K | ~6.6M |
| Roku | ROKU-HONDA-Q1-2026 | $150K | ~4.5M |
| VEVO | VEVO-HONDA-Q1-2026 | $100K | ~4.5M |
| Fox Sports | FOX-HONDA-Q1-2026 | $75K | ~1.8M |

## OEM TIER (10% = $200K)
Device-level targeting with ACR data.

| Publisher | Deal ID | Budget | Est. Impressions |
|-----------|---------|--------|------------------|
| Vizio | VIZIO-HONDA-Q1-2026 | $80K | 4.0M |
| Samsung | SAMG-HONDA-Q1-2026 | $70K | 3.2M |
| LG | LG-HONDA-Q1-2026 | $50K | 2.5M |

TOTAL: $2M across 12 publishers
Est. Impressions: ~60M
Est. Reach: ~17M unique users
Est. Frequency: 3.5
```

---

### **Act 5: Campaign Creation**

Newton creates the Yahoo DSP campaign.

```python
# Step 1: Create campaign container
campaign = mcp_yahoo_dsp.createCampaign(
    advertiser_id="honda_motor_company",
    name="Honda CR-V CTV Q1 2026",
    budget=2000000,
    currency="USD",
    start_date="2026-01-01",
    end_date="2026-03-31",
    goal_type="REACH",
    status="INACTIVE"
)
```

**Response:**
```json
{
  "campaign_id": "camp_abc123def456",
  "order_id": 789012,
  "advertiser_id": "honda_motor_company",
  "name": "Honda CR-V CTV Q1 2026",
  "budget": 2000000,
  "daily_budget": 22222.22,
  "currency": "USD",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31",
  "goal_type": "REACH",
  "status": "INACTIVE"
}
```

---

### **Act 6: Line Creation**

Newton creates lines for each publisher deal.

```python
# Premium Tier Lines
mcp_yahoo_dsp.createLine(
    campaign_id="camp_abc123def456",
    name="Disney Streaming Package",
    budget=300000,
    deal_ids=["DSE-HONDA-Q1-2026"],
    pacing="EVEN",
    frequency_cap={"limit": 3, "duration": 7, "unit": "DAY"},
    targeting={
        "geo_country": ["US"],
        "device_type": ["CTV", "CONNECTED_TV"],
        "daypart": ["PRIMETIME", "LATE_NIGHT"]
    }
)

mcp_yahoo_dsp.createLine(
    campaign_id="camp_abc123def456",
    name="Paramount Streaming Package",
    budget=250000,
    deal_ids=["PARA-HONDA-Q1-2026"],
    pacing="EVEN",
    frequency_cap={"limit": 3, "duration": 7, "unit": "DAY"}
)

mcp_yahoo_dsp.createLine(
    campaign_id="camp_abc123def456",
    name="WBD Streaming Package",
    budget=280000,
    deal_ids=["WBD-HONDA-Q1-2026"],
    pacing="EVEN",
    frequency_cap={"limit": 3, "duration": 7, "unit": "DAY"}
)

# ... Create lines for all 12 publishers
```

**Response (Disney Line):**
```json
{
  "line_id": 1234567,
  "campaign_id": "camp_abc123def456",
  "name": "Disney Streaming Package",
  "budget": 300000,
  "daily_budget": 3333.33,
  "deal_ids": ["DSE-HONDA-Q1-2026"],
  "deals": [
    {
      "deal_id": "DSE-HONDA-Q1-2026",
      "publisher": "Disney Streaming (DSE)",
      "deal_type": "PROGRAMMATIC_GUARANTEED",
      "cpm": 42.0
    }
  ],
  "pacing": "EVEN",
  "bid_strategy": "AUTOBID",
  "max_bid": 46.20,
  "frequency_cap": {
    "limit": 3,
    "duration": 7,
    "duration_unit": "DAY",
    "scope": "LINE"
  },
  "status": "PENDING_REVIEW",
  "media_type": "CTV_VIDEO",
  "estimated": {
    "impressions": 7142857,
    "reach": 2040816,
    "avg_frequency": 3.5,
    "avg_cpm": 42.0
  }
}
```

---

### **Act 7: Creative Sync**

Newton syncs CTV video creatives.

```python
# Sync CTV video creatives
mcp_yahoo_dsp.sync_creatives(
    creatives=[
        {
            "creative_id": "honda_crv_ctv_30s_adventure",
            "name": "Honda CR-V - Adventure Awaits (30s)",
            "format_id": "ctv_video_30s",
            "duration": 30,
            "vast_url": "https://cdn.honda.com/vast/crv_30s_adventure.xml",
            "thumbnail_url": "https://cdn.honda.com/thumbs/crv_30s.jpg",
            "click_through_url": "https://automobiles.honda.com/cr-v"
        },
        {
            "creative_id": "honda_crv_ctv_15s_dealer",
            "name": "Honda CR-V - Find Your Dealer (15s)",
            "format_id": "ctv_video_15s",
            "duration": 15,
            "vast_url": "https://cdn.honda.com/vast/crv_15s_dealer.xml",
            "thumbnail_url": "https://cdn.honda.com/thumbs/crv_15s.jpg",
            "click_through_url": "https://automobiles.honda.com/dealer"
        }
    ]
)
```

---

### **Act 8: Creative Assignment**

Newton assigns creatives to lines.

```python
# Assign 30s creative to Disney line
mcp_yahoo_dsp.createAd(
    line_id=1234567,
    creative_id="honda_crv_ctv_30s_adventure",
    name="CR-V 30s on Disney"
)

mcp_yahoo_dsp.createAd(
    line_id=1234567,
    creative_id="honda_crv_ctv_15s_dealer",
    name="CR-V 15s on Disney"
)

# ... Assign creatives to all lines
```

---

### **Act 9: Delivery Monitoring**

After campaign launches, Newton monitors delivery by publisher.

```python
# Get campaign delivery broken down by deal
mcp_yahoo_dsp.getCampaignDelivery(
    campaign_id="camp_abc123def456",
    breakdown=["deal", "line"]
)
```

**Response:**
```json
{
  "campaign_id": "camp_abc123def456",
  "campaign_name": "Honda CR-V CTV Q1 2026",
  "report_period": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-15"
  },
  
  "totals": {
    "impressions": 9500000,
    "clicks": 47500,
    "spend": 315000,
    "video_completions": 8075000,
    "ctr": 0.005,
    "vcr": 0.85,
    "cpm": 33.16,
    "budget": 2000000,
    "pacing": 0.16
  },
  
  "by_deal": [
    {
      "deal_id": "DSE-HONDA-Q1-2026",
      "publisher": "Disney Streaming (DSE)",
      "deal_type": "PROGRAMMATIC_GUARANTEED",
      "impressions": 1200000,
      "clicks": 7200,
      "spend": 50400,
      "video_completions": 1068000,
      "ctr": 0.006,
      "vcr": 0.89,
      "cpm": 42.0
    },
    {
      "deal_id": "TUBI-HONDA-Q1-2026",
      "publisher": "Tubi",
      "deal_type": "PRIVATE_AUCTION",
      "impressions": 1800000,
      "clicks": 7200,
      "spend": 45000,
      "video_completions": 1440000,
      "ctr": 0.004,
      "vcr": 0.80,
      "cpm": 25.0
    }
    // ... 10 more publishers
  ],
  
  "by_line": [
    {
      "line_id": 1234567,
      "name": "Disney Streaming Package",
      "budget": 300000,
      "spend": 50400,
      "pacing": 0.17,
      "impressions": 1200000,
      "vcr": 0.89,
      "cpm": 42.0
    }
    // ... 11 more lines
  ]
}
```

**Newton's Summary to User:**
```
## Honda CR-V CTV Campaign - Week 2 Report

📊 **DELIVERY STATUS: ON TRACK**

| Metric | Actual | Target | Status |
|--------|--------|--------|--------|
| Spend | $315K | $333K | 95% ⚠️ |
| Impressions | 9.5M | 10M | 95% ✅ |
| VCR | 85% | 80% | 106% ✅ |
| Unique Reach | 2.7M | 2.5M | 108% ✅ |

### TOP PERFORMERS (by VCR):
1. **HBO Max** - 92% VCR, $45 CPM
2. **Disney** - 89% VCR, $42 CPM  
3. **WBD** - 87% VCR, $40 CPM

### EFFICIENCY WINNERS (by CPM):
1. **VEVO** - $20 CPM, 78% VCR
2. **LG** - $20 CPM, 75% VCR
3. **Vizio** - $21 CPM, 76% VCR

### RECOMMENDATION:
- Premium tier (Disney/HBO/WBD) delivering strong completion rates
- Consider shifting 10% from Tubi to HBO Max for better VCR
- OEM tier providing efficient incremental reach

Campaign is on pace to deliver 60M impressions, 17M unique reach.
```

---

## 🔧 Yahoo DSP Tools Reference

### Discovery Tools
| Tool | Endpoint | Purpose |
|------|----------|---------|
| `listDeals` | `/traffic/deals` | List available PMP/PG deals |
| `getDealDetails` | `/traffic/deals/{id}` | Get deal terms and specs |

### Campaign Management
| Tool | Endpoint | Purpose |
|------|----------|---------|
| `createCampaign` | `/traffic/campaigns` | Create campaign container |
| `createLine` | `/traffic/lines` | Create line targeting deals |
| `createAd` | `/traffic/ads` | Associate creative with line |

### Reporting
| Tool | Endpoint | Purpose |
|------|----------|---------|
| `getCampaignDelivery` | Reporting API | Delivery by deal/line |

### Standard AdCP Tools
| Tool | Purpose |
|------|---------|
| `sync_creatives` | Upload CTV video creatives |
| `get_media_buy_delivery` | AdCP-standard delivery |

---

## 📊 Demo Sequence Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HONDA CTV CAMPAIGN - YAHOO DSP                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  USER                    NEWTON                    YAHOO DSP            │
│    │                        │                          │                │
│    │ "Run $2M CTV across    │                          │                │
│    │  12 streaming pubs"    │                          │                │
│    │───────────────────────>│                          │                │
│    │                        │                          │                │
│    │                        │  listDeals()             │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │                        │  [12 deals: DSE, Para,   │                │
│    │                        │   Tubi, WBD, HBO, Fox,   │                │
│    │                        │   Roku, VEVO, Vizio,     │                │
│    │                        │   Samsung, LG, Disc+]    │                │
│    │                        │<─────────────────────────│                │
│    │                        │                          │                │
│    │                        │  getDealDetails() x3     │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │  "Here are available   │                          │                │
│    │   deals and my         │                          │                │
│    │   allocation plan..."  │                          │                │
│    │<───────────────────────│                          │                │
│    │                        │                          │                │
│    │  "Proceed"             │                          │                │
│    │───────────────────────>│                          │                │
│    │                        │                          │                │
│    │                        │  createCampaign()        │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │                        │  createLine() x12        │                │
│    │                        │  (one per deal)          │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │                        │  sync_creatives()        │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │                        │  createAd() x24          │                │
│    │                        │  (2 creatives x 12 lines)│                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │  "Campaign created:    │                          │                │
│    │   12 lines, $2M,       │                          │                │
│    │   60M est. impressions"│                          │                │
│    │<───────────────────────│                          │                │
│    │                        │                          │                │
│    │  [After launch]        │                          │                │
│    │  "Status update?"      │                          │                │
│    │───────────────────────>│                          │                │
│    │                        │                          │                │
│    │                        │  getCampaignDelivery()   │                │
│    │                        │─────────────────────────>│                │
│    │                        │                          │                │
│    │  "Week 2: On track,    │                          │                │
│    │   85% VCR, 2.7M reach" │                          │                │
│    │<───────────────────────│                          │                │
│    │                        │                          │                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🏷️ Deal Types Explained

### Programmatic Guaranteed (PG)
- **Fixed CPM** - Price locked at negotiated rate
- **Guaranteed impressions** - Publisher commits to delivery
- **Premium inventory** - Disney, HBO, Paramount
- **Brand safety** - Editorial control, no UGC

### Private Marketplace (PMP)
- **Floor CPM** - Minimum bid to participate
- **Auction-based** - Win rate depends on bid
- **Large scale** - Tubi, Roku, VEVO
- **Efficient reach** - Lower CPM for volume

### Preferred Deal
- **Fixed CPM** - Negotiated rate
- **Priority access** - First look at inventory
- **OEM inventory** - Vizio, Samsung, LG
- **ACR data** - Cross-device measurement

---

## 📈 Success Metrics

| KPI | Target | Measurement |
|-----|--------|-------------|
| Unique Reach | 17M users | Yahoo DSP reporting |
| Video Completion Rate | 80%+ | VAST events |
| Brand Lift | +5 points | Post-campaign survey |
| Viewability | 90%+ | MRC standard |
| Budget Pacing | 100% | getCampaignDelivery |

---

## 🔄 Alternative Workflows

### Audience Overlay (Optional)
Newton can still use audience segments to overlay on deals:

```python
mcp_yahoo_dsp.createLine(
    campaign_id="camp_abc123def456",
    name="Disney + Auto Intenders",
    budget=150000,
    deal_ids=["DSE-HONDA-Q1-2026"],
    targeting={
        "segment_ids": [98765, 98770],  # Auto intender segments
        "geo_country": ["US"]
    }
)
```

### Performance Optimization
Newton can reallocate budget based on performance:

```python
# Shift budget from underperforming to top performers
mcp_yahoo_dsp.updateLine(
    line_id=1234567,  # Disney (high VCR)
    budget=350000     # Increase from $300K
)

mcp_yahoo_dsp.updateLine(
    line_id=1234568,  # Tubi (lower VCR)
    budget=150000     # Decrease from $175K
)
```
