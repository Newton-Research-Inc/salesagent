# 🎉 Demo Setup Complete!

## What's Been Created

Your AdCP Sales Agent demo environment is now fully configured for Newton (media buyer) testing.

---

## ✅ Completed Tasks

### 1. **Realistic Products Added** ✅

**ESPN (Sports Inventory):**
- ESPN Homepage - Leaderboard ($8-12 CPM, 1M daily impressions)
- Live Game Sidebar - Rectangle ($10-15 CPM, 500k daily impressions)
- ESPN Mobile App - Banner ($5-7 CPM, 2M daily impressions)

**CNN (News Inventory):**
- CNN Homepage - Leaderboard ($10-15 CPM, 1.5M daily impressions)
- Article Sidebar - Wide Skyscraper ($7-10 CPM, 800k daily impressions)
- Breaking News Alert - Banner ($12-18 CPM, 400k daily impressions)

**NYT (Premium Inventory):**
- NYT Homepage - Billboard ($15-22 CPM, 800k daily impressions)
- Article Inline - Rectangle ($12-18 CPM, 600k daily impressions)
- Opinion Section - Leaderboard ($10-14 CPM, 300k daily impressions)

**Total: 9 products across 3 publishers**

### 2. **Campaign Briefs Created** ✅

Three realistic campaign scenarios documented in `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`:

- **Nike Air Jordan Launch** (ESPN, $50k, sports enthusiasts)
- **Coca-Cola Holiday Campaign** (CNN, $75k, brand awareness)
- **Apple Vision Pro** (NYT, $100k, affluent tech audience)

Each brief includes:
- Target audience profiles
- Budget/timeline details
- Performance goals
- Creative requirements
- Buying strategy
- Success criteria

### 3. **Test Scenario Script** ✅

Working Python script (`docs/demo/newton_test_scenario.py`) that demonstrates:
- Discovery: Query each sales agent for products
- Evaluation: Match products to campaign needs
- Purchase: Create media buys
- Monitoring: Check delivery progress

### 4. **Mock Delivery Simulation** ✅

The mock adapter automatically generates realistic delivery data:
- Progress tracking (elapsed vs. total duration)
- Budget pacing simulation
- Impression delivery calculations
- Click-through rate simulation
- Realistic variance (±5%)

**No manual data insertion needed** - delivery metrics are computed dynamically when you call `get_media_buy_delivery`.

---

## Quick Start Testing

### Option 1: Run Test Scenario (Recommended)

```bash
cd /Users/danfinkel/github/opensource/salesagent
python docs/demo/newton_test_scenario.py
```

This will:
1. Discover products from ESPN, CNN, NYT
2. Create 3 media buys (Nike on ESPN, Coca-Cola on CNN, Apple on NYT)
3. Show how to monitor delivery

### Option 2: Test Individual Operations

**Get Products (ESPN):**
```python
from fastmcp.client import Client
from fastmcp.transports import StreamableHttpTransport

headers = {"x-adcp-auth": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"}
transport = StreamableHttpTransport(url="http://localhost:9580/mcp/", headers=headers)
client = Client(transport=transport)

async with client:
    products = await client.call_tool("get_products", {
        "brief": "Sports inventory for basketball campaign"
    })
    print(f"Found {len(products['products'])} products")
```

**Create Media Buy:**
```python
media_buy = await client.call_tool("create_media_buy", {
    "promoted_offering": "Nike Air Jordan",
    "buyer_ref": "test_001",
    "packages": [{
        "package_ref": "pkg_001",
        "product_ref": "espn_homepage_leaderboard",
        "start_date": "2025-12-01",
        "end_date": "2025-12-31",
        "pricing": {"pricing_model": "CPM", "rate": 12.00, "currency": "USD"},
        "inventory_requests": [{"quantity": 1000000, "unit": "IMPRESSIONS"}]
    }]
})
```

**Check Delivery:**
```python
delivery = await client.call_tool("get_media_buy_delivery", {
    "media_buy_ids": [media_buy['media_buy_id']]
})
```

---

## Connection Details (For Newton)

### ESPN Sales Agent
- **URL**: `http://localhost:9580/mcp/`
- **Auth Token**: `adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA`
- **Principal**: Nike Inc.
- **Focus**: Sports inventory, basketball fans

### CNN Sales Agent
- **URL**: `http://localhost:9580/mcp/`
- **Auth Token**: `adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM`
- **Principal**: Coca-Cola
- **Focus**: News inventory, broad audience

### NYT Sales Agent
- **URL**: `http://localhost:9580/mcp/`
- **Auth Token**: `adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo`
- **Principal**: Apple Inc.
- **Focus**: Premium inventory, affluent readers

**Note**: All three agents use the **same MCP URL** but **different auth tokens**. The token determines which tenant (publisher) you're buying from.

---

## Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| **Campaign Briefs** | Detailed campaign specs for Nike, Coca-Cola, Apple | `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md` |
| **Test Scenario** | Working Python script to test complete flow | `docs/demo/newton_test_scenario.py` |
| **Complete Demo Guide** | Comprehensive testing instructions | `docs/demo/COMPLETE_DEMO_GUIDE.md` |
| **Integration Guide** | Newton integration instructions | `NEWTON_INTEGRATION.md` |

---

## Services Status

Check if everything is running:

```bash
docker-compose ps
```

Should show:
- ✅ `salesagent-postgres-1` (healthy) - Port 9532
- ✅ `salesagent-adcp-server-1` (healthy) - Port 9580 (MCP)
- ✅ `salesagent-admin-ui-1` (healthy) - Port 9501

### Health Check

```bash
curl http://localhost:9580/health  # MCP Server
curl http://localhost:9501/health  # Admin UI
```

---

## Key Features Demonstrated

### 1. Multi-Tenant Architecture
- Single MCP server supports 3 independent publishers
- Token-based authentication routes to correct tenant
- Isolated data per publisher

### 2. Product Discovery
- Natural language queries ("sports inventory for basketball fans")
- Returns matching products with pricing, formats, targeting
- Realistic product catalog per publisher

### 3. Media Buy Creation
- Standard AdCP `create_media_buy` tool
- Package-based inventory requests
- CPM pricing, guaranteed delivery
- Mock adapter creates orders instantly

### 4. Delivery Monitoring
- Automatic progress tracking
- Budget pacing simulation
- Realistic impression/click data
- Works immediately (no waiting for real campaigns)

### 5. Mock Adapter Benefits
- No real ad server needed
- Instant campaign creation
- Realistic delivery simulation
- Time-based progress calculation
- Safe for testing/demos

---

## Next Steps for Newton

### Phase 1: Basic Connection (Start Here)
1. Add three DataConnectors in Newton:
   - Name: "ESPN Sales Agent", URL: `http://localhost:9580/mcp/`, Token: ESPN token
   - Name: "CNN Sales Agent", URL: `http://localhost:9580/mcp/`, Token: CNN token  
   - Name: "NYT Sales Agent", URL: `http://localhost:9580/mcp/`, Token: NYT token

2. Test connection:
   ```python
   tools = await newton.mcp_client.list_tools("ESPN Sales Agent")
   # Should return: get_products, create_media_buy, get_media_buy_delivery, etc.
   ```

3. Call `get_products`:
   ```python
   products = await newton.mcp_client.call_tool(
       "ESPN Sales Agent",
       "get_products",
       {"brief": "Sports inventory"}
   )
   ```

### Phase 2: LLM Integration
1. Feed campaign brief + products to Newton's LLM
2. Let LLM evaluate which products match campaign
3. LLM generates `create_media_buy` payload
4. Execute media buy via MCP client

### Phase 3: Monitoring
1. Store media buy IDs from purchases
2. Periodic calls to `get_media_buy_delivery`
3. LLM analyzes delivery vs. goals
4. Suggest optimizations

---

## Troubleshooting

### "No products found"
```bash
# Check products were created
docker-compose exec postgres psql -U adcp_user -d adcp -c \
  "SELECT tenant_id, COUNT(*) FROM products GROUP BY tenant_id;"

# Expected output:
#  tenant_id | count 
# -----------+-------
#  espn      |     3
#  cnn       |     3
#  nyt       |     3
```

### "Authentication failed"
- Check token is exact (no spaces)
- Use `x-adcp-auth` header (not `Authorization`)
- Token must match tenant (espn/cnn/nyt)

### "Delivery shows zero"
- Campaign start date is in the future
- Use past start date to simulate progress:
  ```python
  start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
  ```

### Services not running
```bash
docker-compose up -d  # Start services
docker-compose logs -f adcp-server  # Check logs
```

---

## Success Criteria

You'll know the demo is working when:

✅ Newton can connect to all 3 sales agents  
✅ `get_products` returns 3 products per agent  
✅ `create_media_buy` succeeds and returns media buy ID  
✅ `get_media_buy_delivery` returns realistic delivery data  
✅ Delivery percentages match campaign progress (time elapsed)  
✅ Newton's LLM can evaluate products and make buying decisions

---

## Demo Talking Points

**For External Demos:**
- "Newton acts as an AI media buyer across ESPN, CNN, and NYT"
- "Single AdCP protocol works across all publishers"
- "LLM evaluates products based on campaign objectives"
- "Automated monitoring tracks delivery without manual intervention"
- "Mock adapter provides realistic simulation for safe testing"

**Technical Highlights:**
- Multi-tenant architecture (3 publishers, 1 server)
- Standard AdCP protocol (works with any AdCP-compliant agent)
- Automatic delivery simulation (no manual data entry)
- Production-ready patterns (can replace mock with GAM, Kevel, etc.)

---

## Files Created

```
docs/demo/
├── NEWTON_CAMPAIGN_BRIEFS.md      # Campaign specifications
├── newton_test_scenario.py        # Working test script
└── COMPLETE_DEMO_GUIDE.md         # Comprehensive testing guide

Root:
├── NEWTON_INTEGRATION.md          # Integration instructions
└── DEMO_SETUP_COMPLETE.md         # This file
```

---

**Status**: 🎉 **FULLY CONFIGURED AND READY FOR TESTING**

The demo environment is production-ready with realistic products, campaign briefs, and automated delivery simulation. Newton can now discover inventory, create media buys, and monitor delivery across three publishers using the AdCP protocol.

**Start testing**: Run `python docs/demo/newton_test_scenario.py`


