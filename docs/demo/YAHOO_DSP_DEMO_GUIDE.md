# Yahoo DSP Sales Agent - Demo Guide

## Overview

The Yahoo DSP sales agent simulates a **Demand-Side Platform (DSP)** buying experience, providing Newton with programmatic advertising capabilities alongside the existing direct publisher buys (ESPN, CNN, NYT).

### Key Differences: Direct vs Programmatic

| Feature | Publisher (ESPN/CNN/NYT) | DSP (Yahoo) |
|---------|-------------------------|-------------|
| **Inventory Model** | Owned ad units (placements) | Access to exchanges (supply) |
| **Buying Model** | Direct deals, guaranteed | Programmatic/RTB, auction-based |
| **Targeting Focus** | Placement-first (homepage, sidebar) | Audience-first (demographics, behaviors) |
| **Pricing** | Fixed CPM rates ($5.00) | Bid-based CPM ($5.50-$8.00) |
| **Inventory Type** | Guaranteed delivery | Non-guaranteed (programmatic) |
| **Product Names** | "ESPN Homepage Banner" | "Audience-Targeted Display" |
| **Optimization** | Delivery pacing | Real-time bidding algorithms |
| **Reporting** | Impressions, spend | CTR, conversions, win rates, viewability |

---

## Architecture

### Yahoo DSP Adapter (`src/adapters/yahoo_dsp.py`)

**Programmatic-Specific Features:**
- ✅ **Audience Targeting**: 10+ pre-defined segments (auto_intenders, high_income_households, etc.)
- ✅ **Bid Strategies**: Manual CPM, auto-optimize CTR, auto-optimize CPA, maximize reach
- ✅ **Inventory Sources**: Yahoo Exchange, Verizon Media, Open Exchange, Premium PMPs
- ✅ **Rich Reporting**: Win rates, bid landscape, viewability, conversions
- ✅ **Auction Simulation**: Bid requests, win rate calculation, dynamic pricing

**Supported Pricing Models:**
- CPM (cost per thousand impressions)
- CPC (cost per click)
- CPCV (cost per completed view)
- CPA (cost per acquisition)
- ❌ NO flat_rate (programmatic platforms don't support guaranteed buys)

---

## Demo Products

Yahoo DSP includes **3 programmatic products** (vs publisher placement-based products):

### 1. Audience-Targeted Display
```json
{
  "product_id": "yahoo_display_728x90",
  "name": "Audience-Targeted Display",
  "format": "display_728x90",
  "description": "Reach high-value audiences across Yahoo Exchange + open web",
  "pricing": {
    "model": "CPM",
    "rate": 6.50,
    "is_fixed": false,  // Bid-based, not fixed
    "currency": "USD"
  },
  "targeting_focus": "Audience segments (not placements)"
}
```

**Differentiator:** Price is $6.50 (vs $5.00 for direct) because audience targeting adds value.

### 2. Premium Display + Retargeting
```json
{
  "product_id": "yahoo_display_300x250",
  "name": "Premium Display + Retargeting",
  "format": "display_300x250",
  "description": "Medium rectangle with site retargeting pools",
  "pricing": {
    "model": "CPM",
    "rate": 8.00,
    "is_fixed": false,
    "currency": "USD"
  },
  "targeting_focus": "Retargeting + behavioral audiences"
}
```

**Differentiator:** Highest CPM ($8.00) due to retargeting capabilities.

### 3. Mobile Audience Network
```json
{
  "product_id": "yahoo_display_320x50",
  "name": "Mobile Audience Network",
  "format": "display_320x50",
  "description": "Mobile inventory with behavioral targeting",
  "pricing": {
    "model": "CPM",
    "rate": 5.50,
    "is_fixed": false,
    "currency": "USD"
  },
  "targeting_focus": "Mobile device + audience segments"
}
```

**Differentiator:** Lower CPM ($5.50) but vast mobile reach.

---

## Newton Integration

### MCP Server Configuration

Add Yahoo DSP as the 4th sales agent in Newton's MCP configuration:

```json
{
  "mcpServers": {
    "espn_sales_agent": {
      "url": "http://espn.salesagent.local:9580/mcp",
      "name": "ESPN Sales Agent",
      "type": "publisher"
    },
    "cnn_sales_agent": {
      "url": "http://cnn.salesagent.local:9580/mcp",
      "name": "CNN Sales Agent",
      "type": "publisher"
    },
    "nyt_sales_agent": {
      "url": "http://nyt.salesagent.local:9580/mcp",
      "name": "NYT Sales Agent",
      "type": "publisher"
    },
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp",
      "name": "Yahoo DSP",
      "type": "dsp"
    }
  }
}
```

**Key Difference:** `type: "dsp"` indicates programmatic platform.

---

## Campaign Buying Comparison

### Example: Nike Buys $50K Campaign

#### **Scenario 1: Direct Publisher Buy (ESPN)**

```python
# Newton calls: mcp_espn.get_products()
products = [
  {
    "name": "ESPN Homepage Banner",
    "format": "display_728x90",
    "pricing": "$5.00 CPM (fixed)",
    "targeting": "ESPN Homepage placement",
    "delivery": "Guaranteed"
  }
]

# Newton calls: mcp_espn.create_media_buy()
result = {
  "status": "active",  # Immediately active
  "packages": [
    {
      "product": "ESPN Homepage Banner",
      "budget": $50000,
      "impressions": 10000000,  # 10M impressions at $5 CPM
      "pacing": "even"
    }
  ]
}
```

**Characteristics:**
- ✅ Guaranteed delivery
- ✅ Fixed pricing ($5.00 CPM)
- ✅ Placement-specific (ESPN homepage)
- ✅ Immediate activation
- ❌ Limited targeting (placement only)

---

#### **Scenario 2: Programmatic Buy (Yahoo DSP)**

```python
# Newton calls: mcp_yahoo.get_products()
products = [
  {
    "name": "Audience-Targeted Display",
    "format": "display_728x90",
    "pricing": "$6.50 CPM (bid-based)",
    "targeting": "Audience segments (auto_intenders, high_income)",
    "delivery": "Programmatic (non-guaranteed)"
  }
]

# Newton calls: mcp_yahoo.create_media_buy()
result = {
  "status": "pending_review",  # DSPs review campaigns first
  "packages": [
    {
      "product": "Audience-Targeted Display",
      "budget": $50000,
      "estimated_impressions": 7692307,  # ~7.7M impressions at $6.50 CPM
      "bid_strategy": "auto_optimize_ctr",
      "audience_segments": ["auto_intenders", "high_income_households"],
      "estimated_reach": 2500000  # Unique users
    }
  ],
  "bid_landscape": {
    "median_winning_bid": 6.83,
    "percentile_25": 5.20,
    "percentile_75": 8.13,
    "competition_level": "medium",
    "estimated_win_rate_at_bid": {
      "5.20": 0.25,  # 25% win rate at low bid
      "6.50": 0.45,  # 45% win rate at median
      "7.80": 0.65,  # 65% win rate at high bid
    }
  }
}
```

**Characteristics:**
- ✅ Audience targeting (demographics, behaviors)
- ✅ Dynamic pricing (bid-based)
- ✅ Broader reach across multiple sites (exchange)
- ✅ Performance optimization (auto-bidding)
- ⚠️ Non-guaranteed delivery
- ⚠️ Requires campaign review
- 💰 Higher CPM ($6.50 vs $5.00) for targeting

---

## Performance Reporting

### Publisher (ESPN) - Basic Metrics

```python
# mcp_espn.get_media_buy_delivery()
{
  "packages": [
    {
      "impressions": 5000000,
      "spend": 25000.00,
      "avg_cpm": 5.00,
      "status": "delivering"
    }
  ]
}
```

**Available Metrics:** Impressions, spend, CPM

---

### DSP (Yahoo) - Rich Programmatic Metrics

```python
# mcp_yahoo.get_media_buy_delivery()
{
  "packages": [
    {
      "impressions": 3850000,
      "clicks": 4235,
      "spend": 25025.00,
      "avg_cpm": 6.50,
      "status": "delivering",
      
      # DSP-specific metrics
      "bid_requests": 12500000,  # Total auction opportunities
      "win_rate": 0.308,  # Won 30.8% of auctions
      "avg_bid": 6.50,
      "avg_win_price": 6.82,  # Paid slightly more than bid
      "viewability_rate": 0.72,  # 72% viewable impressions
      "ctr": 0.0011,  # 0.11% click-through rate
      "conversions": 95,  # Post-click conversions
      "conversion_rate": 0.0224,  # 2.24% of clicks converted
      "audience_segments": 2  # Targeting 2 segments
    }
  ]
}
```

**Available Metrics:** All publisher metrics PLUS:
- Bid requests & win rate
- Viewability scores
- Click-through rates
- Conversion tracking
- Audience performance

---

## Campaign Lifecycle Differences

### Publisher (ESPN/CNN/NYT)

```
1. get_products() → Immediate product list
2. create_media_buy() → Status: "active" (immediate)
3. get_media_buy_delivery() → Basic metrics
```

**Timeline:** Active immediately, simple metrics.

---

### DSP (Yahoo)

```
1. get_products() → Product list with bid guidance
2. create_media_buy() → Status: "pending_review"
   ↓
3. Campaign review (simulated) → Status: "approved"
   ↓
4. Learning phase (7 days) → Status: "delivering"
   ↓
5. get_media_buy_delivery() → Rich performance metrics
```

**Timeline:** Delayed activation, learning phase, detailed metrics.

---

## Demo Scenarios

### 1. Direct vs Programmatic Comparison

**Objective:** Show Newton how to choose between direct and programmatic.

```
Nike wants to spend $100K on display ads:

Option A (Direct - ESPN):
- $5.00 CPM fixed
- 20M impressions guaranteed
- ESPN homepage only
- Simple setup, immediate launch

Option B (Programmatic - Yahoo DSP):
- $6.50 CPM bid (variable)
- ~15M impressions estimated
- Across 100+ sites (Yahoo Exchange)
- Audience targeting (auto_intenders)
- Auto-optimization for CTR
- Conversion tracking included

Newton Decision: Split budget ($50K each) to compare performance!
```

---

### 2. Audience Targeting Demo

**Objective:** Show DSP's unique audience capabilities.

```
Nike launches Air Jordan campaign:

ESPN (Placement-based):
- Target: "ESPN Homepage Banner"
- Reach: All ESPN visitors
- No audience filtering

Yahoo DSP (Audience-based):
- Target: "auto_intenders + high_income_households + fitness_enthusiasts"
- Reach: Filtered audience across 100+ sites
- Higher relevance, better conversion rates
```

---

### 3. Budget Optimization

**Objective:** Show auto-bidding in action.

```
Nike sets goal: "Maximize clicks for $50K budget"

Yahoo DSP Response:
- Bid strategy: "auto_optimize_ctr"
- Starting bid: $6.50 CPM
- Auto-adjustments:
  - Mobile: +20% (better CTR)
  - Evening hours: +15% (higher engagement)
  - Weekend: -10% (lower competition)
- Result: 5% more clicks than manual bidding
```

---

## Deployment

### Step 1: Deploy Yahoo DSP

```bash
# Push Docker image
cd /Users/danfinkel/github/opensource/salesagent
docker build -t salesagent:yahoo-dsp .
docker tag salesagent:yahoo-dsp 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:yahoo-dsp
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:yahoo-dsp
```

### Step 2: Deploy Terraform

```bash
cd terraform/environments/staging
terraform init
terraform plan
terraform apply
```

**Expected Output:**
```
✅ Multi-tenant sales agents deployed:
- ESPN: espn.salesagent.local:9580
- CNN: cnn.salesagent.local:9580
- NYT: nyt.salesagent.local:9580
- Yahoo DSP: yahoo.salesagent.local:9580

Cost: ~$120/month for 4 Fargate tasks
```

### Step 3: Verify Deployment

```bash
# Check ECS services
aws ecs describe-services --cluster salesagent-yahoo --services salesagent-yahoo --region us-east-1

# Check Service Discovery
aws servicediscovery list-services --region us-east-1

# Test DNS resolution (from Newton instance)
dig yahoo.salesagent.local
```

### Step 4: Initialize Yahoo Tenant

```bash
# SSH to one of the ECS tasks or run locally
python scripts/setup/init_demo_tenants_aws.py
```

**Expected Output:**
```
Creating tenant: yahoo...
✓ Created CurrencyLimit for yahoo
✓ Created PropertyTag for yahoo
✓ Created AuthorizedProperty for yahoo
✓ Created Principal for yahoo
✓ Created Product: yahoo_display_728x90
✓ Created Product: yahoo_display_300x250
✓ Created Product: yahoo_display_320x50
✅ Created tenant yahoo with products and principal
```

### Step 5: Update Newton Configuration

Add Yahoo DSP to Newton's MCP servers:

```json
{
  "yahoo_dsp": {
    "url": "http://yahoo.salesagent.local:9580/mcp",
    "transport": "http"
  }
}
```

Restart Newton services.

---

## Testing

### Test 1: Get Products

```bash
# Call Yahoo DSP
curl http://yahoo.salesagent.local:9580/mcp/get_products

# Expected: 3 products (Audience-Targeted Display, Premium Display + Retargeting, Mobile Audience Network)
```

### Test 2: Create Campaign

```bash
curl -X POST http://yahoo.salesagent.local:9580/mcp/create_media_buy \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_ref": "nike_dsp_test",
    "brand_manifest": {"name": "Nike", "url": "https://nike.com"},
    "packages": [
      {
        "package_id": "nike_dsp_728x90",
        "product_id": "yahoo_display_728x90",
        "budget": 10000,
        "creative_ids": ["nike_728x90_v1"]
      }
    ]
  }'

# Expected: Status "pending_review", bid_landscape data
```

### Test 3: Get Performance

```bash
curl http://yahoo.salesagent.local:9580/mcp/get_media_buy_delivery?media_buy_id=<campaign_id>

# Expected: Rich metrics (win_rate, viewability, conversions)
```

---

## Newton Buying Flow

### Newton's Decision Tree

```
Newton: "I need to buy display ads for Nike Air Jordan launch."

Step 1: Discover options
- call mcp_espn.get_products()
- call mcp_cnn.get_products()
- call mcp_nyt.get_products()
- call mcp_yahoo.get_products()

Step 2: Analyze differences
ESPN: "ESPN Homepage Banner" - $5.00 CPM (fixed)
Yahoo DSP: "Audience-Targeted Display" - $6.50 CPM (bid-based)

Step 3: Choose strategy
Option A: Guaranteed reach → Choose ESPN (direct buy)
Option B: Targeted audience → Choose Yahoo DSP (programmatic)
Option C: Diversified → Split budget across both

Step 4: Execute buys
- create_media_buy() on selected agents
- Monitor performance across agents
- Optimize based on results
```

---

## Key Takeaways

### For Newton (AI Agent)

✅ **When to use Direct (ESPN/CNN/NYT):**
- Need guaranteed delivery
- Know specific placements work well
- Want simple, predictable pricing
- Immediate campaign launch required

✅ **When to use DSP (Yahoo):**
- Audience targeting is priority
- Want performance optimization (CTR, conversions)
- Need broader reach across multiple sites
- Have time for learning phase
- Want detailed performance analytics

### For Demos

✅ **Showcases AdCP Flexibility:**
- Single protocol works for both direct and programmatic
- Newton can intelligently choose buying strategy
- Demonstrates real-world advertising complexity

✅ **Realistic DSP Behavior:**
- Bid-based pricing (not fixed)
- Campaign approval delays
- Rich performance metrics
- Audience targeting capabilities

---

## Troubleshooting

### Issue: Yahoo DSP returns "Unknown adapter type: yahoo_dsp"

**Fix:** Ensure adapter is registered in `src/adapters/__init__.py`:
```python
from .yahoo_dsp import YahooDSP as YahooDSPAdapter

ADAPTER_REGISTRY = {
    # ...
    "yahoo_dsp": YahooDSPAdapter,
}
```

### Issue: Products not showing audience targeting

**Fix:** Yahoo DSP products should include `targeting_template` with `audiences_any_of`:
```python
"targeting_template": {
    "audiences_any_of": ["auto_intenders", "high_income_households"]
}
```

### Issue: Reporting shows same metrics as publisher

**Fix:** Check `get_media_buy_delivery()` in `yahoo_dsp.py` - should include `metadata` with DSP-specific metrics.

---

## Future Enhancements

### Phase 2 Ideas

1. **Lookalike Audiences:** Expand targeting based on seed audience
2. **Private Marketplace Deals:** Simulate PMP deal IDs
3. **Creative A/B Testing:** Auto-optimize creatives
4. **Attribution Windows:** Multi-touch attribution models
5. **Supply Path Optimization:** Prefer certain exchanges
6. **Brand Safety Filters:** Exclude sensitive content categories

---

## Cost Analysis

### Monthly AWS Costs

**Before Yahoo DSP (3 agents):**
- 3 Fargate tasks: ~$90/month
- RDS PostgreSQL: ~$15/month
- **Total: ~$105/month**

**After Yahoo DSP (4 agents):**
- 4 Fargate tasks: ~$120/month (+$30)
- RDS PostgreSQL: ~$15/month (shared)
- **Total: ~$135/month**

**Cost per agent:** ~$30/month (0.25 vCPU, 512MB RAM)

---

## Summary

The Yahoo DSP sales agent adds **programmatic buying capabilities** to your demo, showcasing:

✅ **Direct vs Programmatic** - Newton can intelligently choose
✅ **Audience Targeting** - Beyond placement-based buying
✅ **Performance Optimization** - Auto-bidding, learning phases
✅ **Rich Analytics** - Win rates, viewability, conversions
✅ **Realistic DSP Behavior** - Approvals, bid landscapes, dynamic pricing

**Result:** A comprehensive demo that covers both traditional publisher buys AND modern programmatic advertising! 🎯

