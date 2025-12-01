# Newton + AdCP Sales Agents - Integration Guide

## 🎉 Overview

This guide shows how to integrate Newton with the AdCP Sales Agents (ESPN, CNN, NYT, Yahoo DSP) for automated media buying demonstrations.

---

## 📋 What's Available

### Sales Agents

| Agent | Publisher | Advertiser | Tenant ID | Ad Server Type |
|-------|-----------|------------|-----------|----------------|
| **ESPN** | ESPN | Nike Inc. | `espn` | Direct (Mock) |
| **CNN** | CNN | Coca-Cola | `cnn` | Direct (Mock) |
| **NYT** | New York Times | Apple Inc. | `nyt` | Direct (Mock) |
| **Yahoo DSP** | Yahoo Exchange | Various | `yahoo` | Programmatic (DSP) |

### MCP Connection Details

**Local Development:**
```
MCP Server: http://localhost:9580/mcp/
A2A Server: http://localhost:9591
Admin UI: http://localhost:9501
```

**AWS Production (Service Discovery):**
```
ESPN:      http://espn.salesagent.local:9580/mcp/
CNN:       http://cnn.salesagent.local:9580/mcp/
NYT:       http://nyt.salesagent.local:9580/mcp/
Yahoo DSP: http://yahoo.salesagent.local:9580/mcp/
```

**Note:** AWS Service Discovery DNS only resolves within VPC

### Authentication Tokens

**Demo Mode:**
- `ADCP_DEMO_MODE=true` - No authentication required
- Useful for testing/demos

**Production Mode:**
- ESPN: `x-adcp-auth: adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA`
- CNN: `x-adcp-auth: adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM`
- NYT: `x-adcp-auth: adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo`
- Yahoo: Generated at runtime (check admin UI)

---

## 🚀 Newton MCP Configuration

### Method 1: Newton MCP Config File

Add to Newton's MCP configuration:

```json
{
  "mcpServers": {
    "espn_sales_agent": {
      "url": "http://espn.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"
      }
    },
    "cnn_sales_agent": {
      "url": "http://cnn.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM"
      }
    },
    "nyt_sales_agent": {
      "url": "http://nyt.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo"
      }
    },
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp"
    }
  }
}
```

### Method 2: Newton DataConnector (Programmatic)

```python
# In Newton's DataConnector model
espn_connector = {
    "name": "ESPN Sales Agent",
    "connector_type": "MCP_SERVER",
    "config": {
        "url": "http://espn.salesagent.local:9580/mcp/",
        "deployment_type": "remote"
    },
    "secrets": {
        "bearer_token": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"
    }
}
```

---

## 📖 Newton Workflow Guide

Newton follows a **4-step AdCP media buying workflow**:

### Step 1: Discovery (Get Products)

Newton asks each sales agent what inventory is available:

```python
# ESPN - Sports inventory
espn_products = get_products(brief="sports, basketball, Nike audience")

# CNN - News inventory  
cnn_products = get_products(brief="news, family, holiday campaigns")

# NYT - Premium news
nyt_products = get_products(brief="premium, tech, affluent audience")

# Yahoo DSP - Programmatic inventory
yahoo_products = get_products(brief="audience targeting, retargeting, conversion optimization")
```

**Newton's Task:** Compare products and recommend best fit for campaign goals.

### Step 2: Creative Sync

Register creatives with selected sales agent(s):

```python
nike_creatives = [
    {
        "creative_id": "nike_air_jordan_728x90",
        "name": "Nike Air Jordan - Leaderboard",
        "format_id": "display_728x90",
        "click_through_url": "https://nike.com/air-jordan",
        "preview_url": "https://placeholder.com/nike_728x90.jpg",
        "assets": {
            "image": {
                "url": "https://placeholder.com/nike_728x90.jpg",
                "width": 728,
                "height": 90
            }
        }
    }
]

sync_creatives(creatives=nike_creatives)
```

**Newton's Task:** Ensure creatives match product formats (728x90, 300x250, 320x50).

### Step 3: Media Buy Creation

Book the campaign:

```python
media_buy = create_media_buy(
    buyer_ref="nike_espn_dec_2024",
    brand_manifest={"name": "Nike", "url": "https://nike.com"},
    start_time="2024-12-01T00:00:00Z",
    end_time="2024-12-31T23:59:59Z",
    packages=[{
        "package_id": "nike_espn_homepage",
        "product_id": "espn_display_728x90",
        "creative_ids": ["nike_air_jordan_728x90"],
        "budget": 25000,
        "impressions": 5000000,
        "pacing": "even",
        "pricing_option_id": "cpm_usd_fixed"
    }]
)
```

**Newton's Task:** Calculate budget allocation and select optimal products.

### Step 4: Delivery Monitoring

Track campaign performance:

```python
delivery = get_media_buy_delivery(media_buy_ids=[media_buy_id])

# Direct buy metrics (ESPN/CNN/NYT)
{
    "impressions": 2500000,
    "clicks": 12500,
    "spend": 12500,
    "avg_cpm": 5.00
}

# Programmatic metrics (Yahoo DSP)
{
    "impressions": 1923076,
    "clicks": 2115,
    "spend": 12500,
    "avg_cpm": 6.50,
    "bid_requests": 8000000,
    "win_rate": 0.24,
    "viewability_rate": 0.72,
    "conversions": 48,
    "conversion_rate": 0.0227
}
```

**Newton's Task:** Interpret metrics and recommend optimizations.

---

## 🎬 Demo Scenarios

### Scenario 1: Budget Split Across Publishers

**Goal:** $50K total, diversify across 3 publishers

```
Newton's Strategy:
- ESPN: $20K (highest reach, sports audience)
- CNN: $15K (news, broad demographics)
- NYT: $15K (premium, affluent)

Rationale: Spread risk, test different audiences
```

### Scenario 2: Direct vs Programmatic

**Goal:** Compare buying strategies

```
Newton's Strategy:
- ESPN (Direct): $25K, guaranteed delivery, simple pricing
- Yahoo DSP (Programmatic): $25K, audience targeting, performance metrics

Week 1 Results:
- ESPN: 5M impressions, $25K spent, basic metrics
- Yahoo DSP: 3.8M impressions, $25K spent, 54 conversions tracked

Newton's Recommendation: Shift more budget to Yahoo DSP for measurable ROI
```

### Scenario 3: Multi-Format Test

**Goal:** Find best-performing creative size

```
Newton's Strategy:
- 728x90 (Leaderboard): $10K
- 300x250 (Rectangle): $10K  
- 320x50 (Mobile): $10K

After 1 week:
- 300x250 has highest CTR (0.15% vs 0.08%)
- Recommendation: Shift budget to 300x250
```

---

## 📊 Campaign Briefs

Pre-configured campaign scenarios for Newton demos:

### Nike Air Jordan Launch
- **Budget:** $50K
- **Duration:** 30 days
- **Target:** Sports enthusiasts, basketball fans
- **Products:** ESPN display inventory (728x90, 300x250)
- **Goal:** Brand awareness, site traffic

### Coca-Cola Holiday Campaign
- **Budget:** $75K
- **Duration:** 45 days
- **Target:** Family-oriented, holiday shoppers
- **Products:** CNN homepage, breaking news
- **Goal:** Seasonal brand lift

### Apple Vision Pro Launch
- **Budget:** $100K
- **Duration:** 60 days
- **Target:** Affluent, tech early adopters
- **Products:** NYT premium placements
- **Goal:** Premium positioning, conversions

See `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md` for full details.

---

## 🔧 Testing the Integration

### Quick Test Script

```bash
cd /Users/danfinkel/github/opensource/salesagent
python docs/demo/newton_test_scenario.py
```

This simulates Newton's workflow:
1. Query all sales agents
2. Create test campaigns
3. Monitor delivery

### Manual MCP Test

```bash
# Test get_products
curl -X POST http://localhost:9580/mcp/tools/get_products/call \
  -H "Content-Type: application/json" \
  -H "x-adcp-auth: adcp_espn_..." \
  -d '{"arguments": {"brief": "sports inventory"}}'

# Test create_media_buy
curl -X POST http://localhost:9580/mcp/tools/create_media_buy/call \
  -H "Content-Type: application/json" \
  -H "x-adcp-auth: adcp_espn_..." \
  -d '{"arguments": {...}}'
```

---

## 🐛 Troubleshooting

### Issue: Newton can't discover MCP tools

**Symptom:** No tools appear in Newton UI

**Fix:**
1. Check MCP server is running: `curl http://localhost:9580/health`
2. Verify Newton's MCP config includes correct URLs
3. Check auth headers are set correctly
4. Restart Newton after config changes

### Issue: "Authentication required by tenant policy"

**Symptom:** All tool calls fail with auth error

**Fix (Demo Mode):**
```bash
# Set environment variable
export ADCP_DEMO_MODE=true

# Or in docker-compose.yml
environment:
  - ADCP_DEMO_MODE=true
```

**Fix (Production Mode):**
- Ensure `x-adcp-auth` header is set with correct token
- Check token format: `adcp_{tenant_id}_{random_string}`

### Issue: "Setup incomplete" error on create_media_buy

**Symptom:** Campaign creation blocked by setup checklist

**Fix:** Either:
1. Enable demo mode (bypasses setup checks)
2. Complete tenant setup via Admin UI (`/tenant/{id}/setup-checklist`)

### Issue: Yahoo DSP DNS doesn't resolve

**Symptom:** `yahoo.salesagent.local` fails to resolve

**Fix:**
- Ensure Newton is in the same VPC as sales agents
- Service Discovery DNS is VPC-only (not public)
- Alternative: Use ALB public endpoint if configured

---

## 📚 Related Documentation

- **Yahoo DSP Guide:** `docs/demo/YAHOO_DSP_GUIDE.md`
- **Campaign Briefs:** `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`
- **Demo Scripts:** `examples/demo/newton_test_scenario.py`
- **MCP Config Example:** `examples/demo/newton_mcp_config_yahoo.json`

---

## ✅ Integration Checklist

After setup, verify:

- [ ] All 4 sales agents running (ESPN, CNN, NYT, Yahoo DSP)
- [ ] Newton can discover tools from each agent
- [ ] `get_products` returns inventory from all agents
- [ ] `create_media_buy` successfully books campaigns
- [ ] `get_media_buy_delivery` returns performance metrics
- [ ] Yahoo DSP shows programmatic metrics (win_rate, conversions, etc.)
- [ ] Newton can compare direct vs programmatic results

---

## 🎉 Result

Newton can now:
- ✅ Query 4 different sales agents for inventory
- ✅ Compare direct publisher buys vs programmatic DSP
- ✅ Create campaigns with budget allocation
- ✅ Monitor performance with rich metrics
- ✅ Make data-driven optimization recommendations

**Demo-ready multi-channel media buying!** 🚀

