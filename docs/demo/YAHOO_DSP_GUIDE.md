# Yahoo DSP Sales Agent - Complete Guide

## 🎯 What is Yahoo DSP?

A **Demand-Side Platform (DSP)** sales agent that simulates **programmatic advertising** alongside direct publisher agents (ESPN, CNN, NYT). This demonstrates how the same AdCP protocol handles both traditional publisher buys AND modern programmatic buying.

---

## 📊 Quick Reference: Direct vs Programmatic

| Feature | Publishers (ESPN/CNN/NYT) | Yahoo DSP |
|---------|--------------------------|-----------|
| **Model** | Direct buy | Programmatic/RTB |
| **Pricing** | $5.00 CPM (fixed) | $5.50-$8.00 CPM (auction) |
| **Targeting** | Placement (homepage, sidebar) | Audience (demographics, behaviors) |
| **Delivery** | Guaranteed | Non-guaranteed |
| **Launch** | Immediate | Requires approval |
| **Metrics** | Basic (impressions, spend) | Rich (win rates, conversions, viewability) |

---

## 🛒 Yahoo DSP Products

### 1. Audience-Targeted Display (728x90)
- **CPM:** $6.50 (bid-based)
- **Focus:** Audience segments + open web reach
- **Use Case:** Brand awareness with targeting
- **Price Guidance:** Floor: $5.00, P50: $6.50, P75: $8.00

### 2. Premium Display + Retargeting (300x250)
- **CPM:** $8.00 (bid-based)
- **Focus:** Site retargeting pools
- **Use Case:** Abandoned cart recovery, conversion optimization
- **Price Guidance:** Floor: $6.00, P50: $8.00, P75: $10.00

### 3. Mobile Audience Network (320x50)
- **CPM:** $5.50 (bid-based)
- **Focus:** Mobile behavioral targeting
- **Use Case:** Mobile-first campaigns, app installs
- **Price Guidance:** Floor: $4.00, P50: $5.50, P75: $7.00

---

## 🏗️ Architecture

### Yahoo DSP Adapter (`src/adapters/yahoo_dsp.py`)

**Programmatic-Specific Features:**
- ✅ **Audience Targeting**: 10+ pre-defined segments (auto_intenders, high_income_households, etc.)
- ✅ **Bid Strategies**: Manual CPM, auto-optimize CTR, auto-optimize CPA, maximize reach
- ✅ **Inventory Sources**: Yahoo Exchange, Verizon Media, Open Exchange, Premium PMPs
- ✅ **Rich Reporting**: Win rates, bid landscape, viewability, conversions
- ✅ **Auction Simulation**: Bid requests, win rate calculation, dynamic pricing

**Supported Pricing Models:**
- CPM, CPC, CPCV, CPA (no flat_rate - programmatic only)

**Key Implementation Details:**
```python
class YahooDSP(AdServerAdapter):
    adapter_name = "yahoo_dsp"
    
    SUPPORTED_AUDIENCE_SEGMENTS = {
        "auto_intenders", "high_income_households", "recent_purchasers",
        "travel_enthusiasts", "tech_early_adopters", "luxury_shoppers",
        "fitness_enthusiasts", "home_improvement", "pet_owners"
    }
    
    SUPPORTED_BIDDING_STRATEGIES = {
        "manual_cpm", "auto_optimize_ctr", "auto_optimize_cpa",
        "maximize_reach", "target_frequency"
    }
```

---

## 🚀 Deployment Guide

### Prerequisites
- AWS account with ECR access
- Terraform installed
- Docker with AMD64 support
- Newton in same VPC (for Service Discovery DNS)

### Step 1: Build and Push Docker Image

```bash
cd /Users/danfinkel/github/opensource/salesagent

# Build for AMD64 (critical for ECS compatibility)
docker build --platform linux/amd64 -t salesagent:yahoo-dsp .

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  381492092437.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag salesagent:yahoo-dsp \
  381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest
```

### Step 2: Deploy with Terraform

```bash
cd terraform/environments/staging
terraform plan  # Review Yahoo DSP addition
terraform apply  # Type 'yes' when prompted
```

### Step 3: Verify Deployment

```bash
# Check ECS service
aws ecs describe-services \
  --cluster salesagent-yahoo \
  --services salesagent-yahoo \
  --region us-east-1

# Check Service Discovery
aws servicediscovery list-services --region us-east-1 | grep yahoo

# Test from Newton VPC
curl http://yahoo.salesagent.local:9580/mcp/
```

### Step 4: Update Newton Configuration

```json
{
  "mcpServers": {
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp"
    }
  }
}
```

Restart Newton to load new MCP server.

---

## 📍 Service Discovery DNS

All four sales agents use stable DNS names (no more IP changes):

```
ESPN:      espn.salesagent.local:9580
CNN:       cnn.salesagent.local:9580
NYT:       nyt.salesagent.local:9580
Yahoo DSP: yahoo.salesagent.local:9580
```

**Note:** DNS only resolves within VPC

---

## 🎬 Demo Scenarios

### Scenario 1: Direct vs Programmatic Comparison

```
Nike needs $50K in display ads

ESPN (Direct):
→ $5.00 CPM × 10M impressions = $50K
→ Guaranteed delivery
→ ESPN homepage only
→ Immediate launch

Yahoo DSP (Programmatic):
→ $6.50 CPM × ~7.7M impressions = $50K
→ Auction-based (non-guaranteed)
→ Across 100+ sites
→ Audience targeting (auto_intenders)
→ Auto-optimization
→ Requires approval

Newton Decision: Split budget ($25K each) to compare!
```

### Scenario 2: Audience Targeting Showcase

```
Nike Air Jordan campaign

ESPN (Placement):
- Target: ESPN Homepage Banner
- Reach: ALL ESPN visitors (broad, untargeted)

Yahoo DSP (Audience):
- Target: auto_intenders + fitness_enthusiasts + high_income
- Reach: Filtered audience across 100+ sites
→ Higher relevance → Better conversion rates
```

### Scenario 3: Performance Optimization

```
Goal: Maximize clicks for $50K budget

Yahoo DSP Auto-Bidding:
- Strategy: auto_optimize_ctr
- Mobile: +20% bid (better CTR observed)
- Evening: +15% bid (higher engagement)
- Weekend: -10% bid (lower competition)
→ Result: 5% more clicks than manual bidding
```

---

## 📊 Performance Metrics Comparison

### ESPN (Basic Metrics)
```json
{
  "impressions": 10000000,
  "spend": 50000,
  "avg_cpm": 5.00
}
```

### Yahoo DSP (Rich Programmatic Metrics)
```json
{
  "impressions": 7692307,
  "clicks": 8461,
  "spend": 50000,
  "avg_cpm": 6.50,
  
  "bid_requests": 32000000,
  "win_rate": 0.24,
  "avg_win_price": 6.82,
  "viewability_rate": 0.72,
  "ctr": 0.0011,
  "conversions": 190,
  "conversion_rate": 0.0225,
  "audience_segments": 3
}
```

---

## 🎯 When to Use Each

### Use Direct (ESPN/CNN/NYT) When:
- ✅ Need guaranteed delivery
- ✅ Know specific placements work well
- ✅ Want simple, predictable pricing
- ✅ Need immediate campaign launch

### Use DSP (Yahoo) When:
- ✅ Audience targeting is priority
- ✅ Want performance optimization (CTR, conversions)
- ✅ Need broader reach across multiple sites
- ✅ Have time for learning phase
- ✅ Want detailed performance analytics

---

## 🐛 Troubleshooting

### Issue: `exec /bin/bash: exec format error`

**Cause:** Docker image built for wrong architecture (ARM64 vs AMD64)

**Fix:**
```bash
# Rebuild for AMD64
docker build --platform linux/amd64 -t salesagent:yahoo-dsp .
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# Force ECS redeploy
aws ecs update-service \
  --cluster salesagent-yahoo \
  --service salesagent-yahoo \
  --force-new-deployment \
  --region us-east-1
```

### Issue: Database constraint violation

**Symptom:** `check_auction_has_price_guidance` error

**Cause:** Auction pricing (`is_fixed=false`) requires `price_guidance`

**Fix:** Already fixed in latest code - Yahoo DSP products include price_guidance

### Issue: "Unknown adapter type: yahoo_dsp"

**Cause:** Adapter not registered

**Fix:** Check `src/adapters/__init__.py` includes:
```python
from .yahoo_dsp import YahooDSP as YahooDSPAdapter
ADAPTER_REGISTRY = {"yahoo_dsp": YahooDSPAdapter, ...}
```

### Issue: Products showing $5.00 CPM instead of $6.50

**Cause:** Yahoo tenant not initialized with DSP products

**Fix:** Re-run initialization:
```bash
python scripts/setup/init_demo_tenants_aws.py
```

### Issue: Newton can't resolve yahoo.salesagent.local

**Cause:** Newton not in same VPC

**Fix:** Ensure Newton is in VPC `vpc-0c3f93c08fc1d2530` (Service Discovery DNS is VPC-only)

---

##💰 Cost Analysis

### Monthly AWS Costs

**Before Yahoo DSP:**
- 3 Fargate tasks: ~$90/month
- RDS PostgreSQL: ~$15/month
- **Total: ~$105/month**

**After Yahoo DSP:**
- 4 Fargate tasks: ~$120/month (+$30)
- RDS PostgreSQL: ~$15/month (shared)
- **Total: ~$135/month**

**Cost per agent:** $30/month (0.25 vCPU, 512MB RAM)

---

## 📚 Implementation Reference

### Files Created/Modified

**New Files:**
- `src/adapters/yahoo_dsp.py` (730 lines) - DSP adapter
- `docs/demo/YAHOO_DSP_GUIDE.md` (this file)

**Modified Files:**
- `src/adapters/__init__.py` - Adapter registration
- `scripts/setup/init_demo_tenants_aws.py` - Yahoo tenant
- `terraform/environments/staging/main.tf` - ECS module

**Total new code:** ~750 lines (mostly yahoo_dsp.py)

### Architecture Pattern

Yahoo DSP reuses all shared infrastructure:
- ✅ Same MCP tools (`get_products`, `create_media_buy`, etc.)
- ✅ Same database schema (multi-tenant)
- ✅ Same Admin UI
- ✅ Same A2A server
- 🆕 New adapter (implements DSP-specific behavior)

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Yahoo DSP ECS service is ACTIVE with 1 running task
- [ ] Service Discovery DNS `yahoo.salesagent.local` resolves
- [ ] `curl http://yahoo.salesagent.local:9580/mcp/` returns MCP server info
- [ ] `get_products` returns 3 Yahoo DSP products
- [ ] Product names mention "Audience-Targeted" or "Retargeting"
- [ ] Pricing shows `is_fixed: false` (bid-based)
- [ ] Newton has 4 MCP servers registered
- [ ] Newton can create campaigns on Yahoo DSP
- [ ] Campaign response includes `bid_landscape` data
- [ ] Performance metrics include `win_rate`, `viewability_rate`, `conversions`

---

## 🎉 What This Enables

**Before:** 3 publisher agents (direct buys only)
**After:** 3 publishers + 1 DSP (direct + programmatic)

**Newton can now:**
- ✅ Compare buying strategies (direct vs programmatic)
- ✅ Choose optimal channel per goal
- ✅ Split budgets for diversification
- ✅ Optimize based on performance data
- ✅ Demonstrate AdCP protocol flexibility

---

## 📖 Related Documentation

- **Newton Demo Script:** `docs/demo/NEWTON_YAHOO_DSP_DEMO_SCRIPT.md`
- **Newton Integration:** `docs/demo/NEWTON_INTEGRATION_GUIDE.md`
- **Campaign Briefs:** `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`
- **Source Code:** `src/adapters/yahoo_dsp.py`
- **Terraform Guide:** `terraform/AWS_SETUP_GUIDE.md`

---

**Result:** A demo-ready advertising ecosystem showcasing both direct and programmatic buying! 🚀

