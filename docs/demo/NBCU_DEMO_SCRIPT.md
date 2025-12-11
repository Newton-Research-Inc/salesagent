# NBCU Linear + Streaming Demo Script

## Overview

This demo showcases an agentic media buying workflow where an agency (buying for Honda) negotiates a cross-platform Linear + Streaming buy on NBCU's Sunday Night Football (SNF) inventory.

**Scenario:**
- **Advertiser**: Honda
- **Campaign**: Q1 2026 Sunday Night Football
- **Channels**: Linear TV + Peacock Streaming
- **Audience**: P2+ (Persons 2+)
- **Unit Length**: :30 spots only

## Available MCP Tools

| Tool | Purpose |
|------|---------|
| `getProducts` | Get available NBCU inventory |
| `getMeasurement` | Calculate cross-platform reach/frequency |
| `savePlan` | Book the plan and get confirmation |
| `clearNBCUDemoData` | Reset demo state |

---

## Demo Script

### ACT 1: Discovery

**Agency Prompt:**
> "I am looking to buy Live Sports across Linear & Digital streaming (direct IO) in Q1 2026 for Honda. What do you have available?"

**Newton Response:**
Newton should identify available event types:
- Sunday Night Football (SNF)
- NBA
- Golden Globes

---

### ACT 2: Inventory Request

**Agency Prompt:**
> "Great, we'd like to explore SNF. Please give us your available inventory including dates, unit costs, :30s only, per unit impression estimates, and CPMs. We have $2M budget available for 30 sec spots across Linear & Direct IO. Looking for Audience P2+."

**Newton Action:**
Call `getProducts`:
```json
{
  "flightStartDate": "2025-12-29",
  "flightEndDate": "2026-01-26",
  "advertiser": "Honda",
  "audience": "P2+",
  "division": "SPORTS",
  "subDivision": "SNF"
}
```

**Expected Response:**
| Game | Date | Unit Price | Impressions | CPM | Avails |
|------|------|------------|-------------|-----|--------|
| NFL Game 20 - TBD vs TBD | 01/04/26 | $443,171 | 21M | $21.07 | 19.5 |
| NFL Game 21 - WILDCARD | 01/11/26 | $658,952 | 31M | $21.07 | 0.5 |
| NFL Game 22 - DIVISIONAL | 01/18/26 | $803,620 | 38M | $21.07 | 3.5 |
| NFL Game 23 - CONFERENCE | 01/26/26 | $950,000 | 45M | $21.11 | 2.0 |

---

### ACT 3: Budget Allocation

**Agency Prompt:**
> "How do you recommend we split our $2M budget across Linear & Streaming to maximize reach?"

**Newton Response:**
Newton should recommend a split based on typical cross-platform optimization:
- **Linear**: 85-90% for broad reach during live games
- **Streaming**: 10-15% for incremental reach on Peacock

**Example Recommendation:**
- Linear: $1.75M (87.5%)
- Streaming: $250K (12.5%)

---

### ACT 4: Plan Building

**Agency Prompt:**
> "Let's build a plan with 2 units in the Divisional game and 1 unit in the Conference game on linear. Allocate $150K to streaming at the standard CPM. Please provide cross-platform reach estimates."

**Newton Action:**
Call `getMeasurement`:
```json
{
  "linearPlan": [
    {
      "salesUnitId": 786370,
      "weekOfDate": "2026-01-12",
      "numUnits": 2,
      "unitLength": 30,
      "unitPrice": 803620,
      "impressions": 76280000
    },
    {
      "salesUnitId": 786374,
      "weekOfDate": "2026-01-19",
      "numUnits": 1,
      "unitLength": 30,
      "unitPrice": 950000,
      "impressions": 45000000
    }
  ],
  "digitalPlan": [
    {
      "budget": 150000,
      "CPM": 33.89,
      "unitLengths": [30]
    }
  ]
}
```

**Expected Response:**
```json
{
  "linear": {
    "budget": 2557240,
    "impressions": 121280000,
    "CPM": 21.09,
    "estReach": 109152000,
    "estFrequency": 1.11
  },
  "digital": {
    "budget": 150000,
    "impressions": 4427555,
    "CPM": 33.89,
    "estReach": 1461093,
    "estFrequency": 3.03
  },
  "crossPlatform": {
    "budget": 2707240,
    "impressions": 125707555,
    "CPM": 21.54,
    "estReach": 110393929,
    "estFrequency": 1.14
  }
}
```

---

### ACT 5: Order Confirmation

**Agency Prompt:**
> "Great, let's go to ORDER with this plan. Attached are our buying guidelines/T&Cs. Please confirm the booking and provide creative specs."

**Newton Action:**
Call `savePlan`:
```json
{
  "linearPlan": [
    {
      "salesUnitId": 786370,
      "weekOfDate": "2026-01-12",
      "numUnits": 2,
      "unitLength": 30,
      "unitPrice": 803620,
      "impressions": 76280000
    },
    {
      "salesUnitId": 786374,
      "weekOfDate": "2026-01-19",
      "numUnits": 1,
      "unitLength": 30,
      "unitPrice": 950000,
      "impressions": 45000000
    }
  ],
  "digitalPlan": [
    {
      "budget": 150000,
      "CPM": 33.89,
      "unitLengths": [30]
    }
  ]
}
```

**Newton Response Should Include:**

1. **Booking Confirmation:**
   > "✅ Your Honda SNF Q1 2026 deal is booked!"
   > 
   > **Plan ID:** 101
   > **Total Budget:** $2,707,240
   > **Cross-Platform Reach:** 110.4M P2+
   > **Estimated Frequency:** 1.14x

2. **Creative Specs:**
   > **Linear Specs:** https://together.nbcuni.com/ad-specs/
   > **Streaming Specs:** https://together.nbcuni.com/ad-specs/streaming/
   > 
   > Please send creative and traffic instructions through MediaOcean/OMNI.

3. **Next Steps:**
   > We will provide weekly pacing and delivery updates.

---

## Quick Reference Commands

**Start Fresh:**
> "Clear all NBCU demo data so we can start fresh"

**Full Discovery:**
> "Show me all available NBCU Sports inventory from December 2025 through January 2026 for Honda"

**Specific Inventory:**
> "Get SNF inventory for Honda, P2+ audience, from 12/29/2025 to 1/26/2026"

**Calculate Reach:**
> "Calculate cross-platform reach for 2 units in the Divisional game at $803,620 each with $150K in streaming at $33.89 CPM"

**Book Plan:**
> "Book this plan and provide confirmation with creative specs"

---

## Sample Inventory Data

### Sunday Night Football (SNF)
| salesUnitId | Event | Week Of | Unit Price | Impressions | CPM | Avails |
|-------------|-------|---------|------------|-------------|-----|--------|
| 786362 | Game 20 - TBD vs TBD | 2025-12-29 | $443,171 | 21M | $21.07 | 19.5 |
| 786366 | Game 21 - WILDCARD | 2026-01-05 | $658,952 | 31M | $21.07 | 0.5 |
| 786370 | Game 22 - DIVISIONAL | 2026-01-12 | $803,620 | 38M | $21.07 | 3.5 |
| 786374 | Game 23 - CONFERENCE | 2026-01-19 | $950,000 | 45M | $21.11 | 2.0 |

### NBA
| salesUnitId | Event | Week Of | Unit Price | Impressions | CPM | Avails |
|-------------|-------|---------|------------|-------------|-----|--------|
| 800100 | Christmas Day - LAL vs GSW | 2025-12-22 | $325,000 | 15M | $21.67 | 8.0 |
| 800105 | NBA Primetime | 2026-01-05 | $185,000 | 9.5M | $19.47 | 12.0 |

### Entertainment
| salesUnitId | Event | Week Of | Unit Price | Impressions | CPM | Avails |
|-------------|-------|---------|------------|-------------|-----|--------|
| 850200 | Golden Globes 2026 | 2026-01-05 | $425,000 | 18M | $23.61 | 5.0 |

---

## Key Negotiation Points (Real Demo)

When demoing with real negotiation variables:

1. **Unit Rates**: Will be populated with Honda's negotiated rates (Gross and NET)
2. **CPM Rates**: Streaming CPM based on RPA negotiated rates
3. **Frequency**: RPA negotiated frequency cap for digital
4. **Audience**: P2+ using Nielsen measurement

---

## Tool Schema Reference

### getProducts
```typescript
{
  flightStartDate: string,    // YYYY-MM-DD
  flightEndDate: string,      // YYYY-MM-DD
  advertiser: string,         // e.g., "Honda"
  audience?: string,          // default: "P2+"
  division?: string,          // "SPORTS", "ENTERTAINMENT", "NEWS"
  subDivision?: string        // "SNF", "NBA", "MLB", etc.
}
```

### getMeasurement
```typescript
{
  linearPlan: [{
    salesUnitId: number,
    weekOfDate: string,       // YYYY-MM-DD
    numUnits: number,
    unitLength: number,       // typically 30
    unitPrice: number,
    impressions: number
  }],
  digitalPlan: [{
    budget: number,
    CPM: number,
    unitLengths: number[]     // e.g., [30]
  }]
}
```

### savePlan
Same input as `getMeasurement`, returns:
```typescript
{
  linearPlanId: number,
  planMeasurement: {
    linear: { budget, impressions, CPM, estReach, estFrequency },
    digital: { budget, impressions, CPM, estReach, estFrequency },
    crossPlatform: { budget, impressions, CPM, estReach, estFrequency }
  }
}
```

