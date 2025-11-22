# Complete Newton Demo Guide

## 🎉 Demo Environment Ready!

All components are now set up for a complete media buying demonstration with Newton as the buyer agent.

---

## What's Been Set Up

### ✅ 1. Three Sales Agents (Publishers)

**ESPN** - Sports Inventory
- 3 products (homepage, live games, mobile)
- Floor CPM: $5-10
- Audience: Sports enthusiasts, basketball fans
- Daily impressions: 500k-2M per product

**CNN** - News Inventory
- 3 products (homepage, articles, breaking news)
- Floor CPM: $7-12
- Audience: News consumers, educated professionals
- Daily impressions: 400k-1.5M per product

**NYT** - Premium News Inventory
- 3 products (homepage, articles, opinion)
- Floor CPM: $10-15
- Audience: Affluent, educated readers
- Daily impressions: 300k-800k per product

### ✅ 2. Advertisers (Principals)

- **Nike** (ESPN) - Token: `adcp_espn_Zgdy...`
- **Coca-Cola** (CNN) - Token: `adcp_cnn_bCLg...`
- **Apple** (NYT) - Token: `adcp_nyt_yCJn...`

### ✅ 3. Campaign Briefs

Located in: `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`

- Nike Air Jordan Launch ($50k, sports focus)
- Coca-Cola Holiday Campaign ($75k, brand awareness)
- Apple Vision Pro ($100k, premium positioning)

### ✅ 4. Test Scenario Script

Located in: `docs/demo/newton_test_scenario.py`

Demonstrates complete flow: Discovery → Purchase → Monitoring

### ✅ 5. Mock Delivery Simulation

The mock adapter **automatically generates realistic delivery data** when you query campaigns:

**How it Works:**
1. Tracks campaign progress (elapsed time vs. total duration)
2. Calculates spend based on daily budget and pacing
3. Simulates impressions delivered (using $10 CPM baseline)
4. Adds realistic variance (±5%) to mimic real-world delivery
5. Generates clicks (CTR varies by product/audience)

**Example Delivery Data:**
- Campaign starts: 0 impressions, $0 spend
- Mid-campaign (50% complete): ~50% of budget spent, proportional impressions
- Campaign end (100% complete): 95-105% of budget spent (realistic variance)

---

## Running the Demo

### Option 1: Quick Test (Python Script)

```bash
cd /Users/danfinkel/github/opensource/salesagent
python docs/demo/newton_test_scenario.py
```

This will:
1. Query all 3 sales agents for products
2. Create 3 media buys (one on each platform)
3. Show how to monitor delivery

**Note**: You'll need `fastmcp` installed:
```bash
pip install fastmcp
```

### Option 2: Test with Newton's MCP Client

If Newton is already configured with the three sales agents as DataConnectors:

```python
# In Newton's momentum agent or tool
from newton.mcp_integration.tool_bridge import MCPToolBridge

# Get products from ESPN
espn_products = await mcp_bridge.call_tool(
    connector_id="espn_sales_agent",  # Your DataConnector name
    tool_name="get_products",
    arguments={"brief": "Display inventory for sports brand"}
)

# Create media buy on ESPN
media_buy = await mcp_bridge.call_tool(
    connector_id="espn_sales_agent",
    tool_name="create_media_buy",
    arguments={
        "promoted_offering": "Nike Air Jordan",
        "buyer_ref": "newton_nike_001",
        "packages": [...]  # Package configuration
    }
)

# Monitor delivery (can be called immediately, returns current progress)
delivery = await mcp_bridge.call_tool(
    connector_id="espn_sales_agent",
    tool_name="get_media_buy_delivery",
    arguments={"media_buy_ids": [media_buy["media_buy_id"]]}
)
```

### Option 3: Manual Testing with curl

**1. List available tools:**
```bash
curl -X POST http://localhost:9580/mcp/ \
  -H "Content-Type: application/json" \
  -H "x-adcp-auth: adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

**2. Get products:**
```bash
curl -X POST http://localhost:9580/mcp/ \
  -H "Content-Type: application/json" \
  -H "x-adcp-auth: adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_products",
      "arguments": {
        "brief": "Sports inventory for basketball campaign"
      }
    },
    "id": 2
  }'
```

---

## Testing Delivery Monitoring

### Immediate Monitoring (Campaign Not Started)

Create a media buy with a future start date:
```python
{
    "start_date": "2025-12-01",  # Future date
    "end_date": "2025-12-31"
}
```

Call `get_media_buy_delivery` immediately:
```python
delivery = get_media_buy_delivery(media_buy_id)
# Returns: 0 impressions, $0 spend (campaign hasn't started)
```

### Simulate Time Progression

To see realistic delivery data, create a campaign that "started" in the past:

```python
from datetime import datetime, timedelta

# Campaign started 10 days ago
start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
end_date = (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d")

# Create media buy with past start date
media_buy = create_media_buy({
    "start_date": start_date,  # 10 days ago
    "end_date": end_date,       # 20 days from now
    "packages": [
        {
            "pricing": {"rate": 12.00, "currency": "USD"},
            "inventory_requests": [{"quantity": 3000000, "unit": "IMPRESSIONS"}]
        }
    ]
})

# Check delivery - should show ~33% complete (10 of 30 days)
delivery = get_media_buy_delivery(media_buy_id)
# Returns: ~1M impressions delivered, ~$12k spend
```

### Mock Delivery Formulas

**Budget Calculation:**
```python
total_budget = quantity * (rate / 1000)  # Impressions * CPM
# Example: 3,000,000 * ($12 / 1000) = $36,000
```

**Progress Calculation:**
```python
progress_ratio = elapsed_days / total_days
spend_delivered = total_budget * progress_ratio * variance
impressions_delivered = spend_delivered / (rate / 1000)
```

**Variance:**
- Random factor between 0.95-1.05 (±5%)
- Simulates real-world delivery fluctuations

**Clicks:**
- CTR varies by product type: 0.1%-1.5%
- Higher for engaged placements (live games, breaking news)
- Lower for run-of-site inventory

---

## Example Delivery Data

### Scenario: Nike Campaign on ESPN (Day 10 of 30)

**Campaign Setup:**
- Budget: $48,000 (4M impressions @ $12 CPM)
- Duration: 30 days
- Current: Day 10 (33.3% complete)

**Expected Delivery:**
```json
{
  "media_buy_id": "mb_espn_nike_001",
  "status": "active",
  "packages": [
    {
      "package_id": "pkg_001",
      "product_ref": "espn_homepage_leaderboard",
      "delivery_stats": {
        "impressions_delivered": 1320000,      // ~33% of 4M (with variance)
        "impressions_goal": 4000000,
        "spend_delivered": 15840.00,           // ~33% of $48k
        "spend_goal": 48000.00,
        "clicks_delivered": 13200,             // 1% CTR (sports engaged audience)
        "ctr": 0.01,
        "completion_percentage": 33.0
      }
    }
  ],
  "totals": {
    "impressions": 1320000,
    "spend": 15840.00,
    "clicks": 13200,
    "ctr": 0.01
  },
  "currency": "USD"
}
```

---

## Newton Integration Patterns

### Pattern 1: Discovery Across Multiple Agents

```python
async def discover_inventory_for_campaign(campaign_brief):
    """Newton discovers inventory across all available sales agents."""
    
    all_products = []
    
    for agent_name in ["ESPN", "CNN", "NYT"]:
        products = await mcp_client.call_tool(
            agent_name,
            "get_products",
            {"brief": campaign_brief}
        )
        
        # Enrich with agent context
        for product in products:
            product['agent_name'] = agent_name
            product['agent_audience'] = AGENT_PROFILES[agent_name]['audience']
        
        all_products.extend(products)
    
    return all_products
```

### Pattern 2: LLM-Based Product Selection

```python
async def select_best_products(campaign_brief, available_products):
    """Let LLM evaluate which products best match campaign needs."""
    
    prompt = f"""
    Campaign Brief: {campaign_brief}
    
    Available Products:
    {json.dumps(available_products, indent=2)}
    
    Analyze each product and select the top 3 that best match:
    1. Target audience alignment
    2. Budget efficiency (CPM vs. budget)
    3. Inventory quality (viewability, engagement)
    
    Return: Selected product IDs with rationale
    """
    
    # LLM evaluates and returns selections
    selections = await llm.generate(prompt)
    return selections
```

### Pattern 3: Budget Optimization

```python
async def optimize_budget_allocation(total_budget, selected_products):
    """Distribute budget across selected products for maximum impact."""
    
    allocations = []
    
    for product in selected_products:
        # Calculate recommended allocation based on:
        # - Product CPM
        # - Daily impressions available
        # - Campaign duration
        # - Audience quality score
        
        allocation = {
            'product_id': product['product_id'],
            'agent': product['agent_name'],
            'budget': calculate_optimal_budget(product, total_budget),
            'impressions': budget_to_impressions(allocation['budget'], product['cpm']),
            'rationale': product['selection_rationale']
        }
        
        allocations.append(allocation)
    
    return allocations
```

### Pattern 4: Continuous Monitoring

```python
async def monitor_campaign_performance(media_buy_ids):
    """Newton continuously monitors all active campaigns."""
    
    for media_buy_id in media_buy_ids:
        delivery = await mcp_client.call_tool(
            agent_for_media_buy(media_buy_id),
            "get_media_buy_delivery",
            {"media_buy_ids": [media_buy_id]}
        )
        
        # Check for issues
        if delivery['completion_percentage'] < expected_pacing:
            # Alert: Under-delivering
            await optimize_pacing(media_buy_id)
        
        if delivery['ctr'] < expected_ctr:
            # Alert: Poor creative performance
            await suggest_creative_optimization(media_buy_id)
```

---

## Troubleshooting

### Products Not Appearing
```bash
# Check if products were created successfully
docker-compose exec postgres psql -U adcp_user -d adcp -c "SELECT tenant_id, product_id, name FROM products;"
```

### Delivery Data Shows Zero
- Campaign start date is in the future
- Use a past start date to simulate progress
- Example: `start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")`

### Authentication Errors
- Verify token matches exactly (no extra spaces)
- Check token is for the correct tenant (espn/cnn/nyt)
- Token must be in `x-adcp-auth` header (not `Authorization`)

### No Response from MCP Server
```bash
# Check server is running
docker-compose ps

# Check MCP server logs
docker-compose logs -f adcp-server
```

---

## Next Steps for Newton Integration

### Phase 1: Basic Integration (1-2 hours)
1. ✅ Configure Newton's MCP client with 3 sales agents
2. ✅ Test connection to each agent
3. ✅ Call `get_products` from Newton's momentum agent
4. ✅ Display returned products to user

### Phase 2: LLM-Based Decision Making (2-3 hours)
1. Feed campaign brief + products to LLM
2. Let LLM select best-matching products
3. Generate `create_media_buy` payload
4. Execute media buy

### Phase 3: Monitoring & Optimization (3-4 hours)
1. Store created media buy IDs
2. Periodic calls to `get_media_buy_delivery`
3. LLM analyzes delivery vs. goals
4. Suggests optimizations (budget reallocation, creative changes)

### Phase 4: Multi-Agent Orchestration (4-6 hours)
1. Parallel discovery across all agents
2. Budget optimization across platforms
3. Pacing coordination
4. Unified reporting dashboard

---

## Demo Talking Points

**For Newton as Media Buyer:**
- "Newton discovers inventory across ESPN, CNN, and NYT simultaneously"
- "LLM evaluates which products best match the campaign brief"
- "Newton creates media buys with a single tool call per platform"
- "Continuous monitoring shows real-time delivery progress"
- "Mock adapter provides realistic delivery simulation without real ad servers"

**Key Advantages:**
- **Unified Interface**: Same AdCP tools work across all publishers
- **AI-Driven Decisions**: LLM evaluates products based on campaign needs
- **Automated Monitoring**: Newton checks delivery without manual intervention
- **Safe Testing**: Mock adapter provides realistic behavior without spending real money

---

## Files Reference

- **Campaign Briefs**: `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`
- **Test Scenario**: `docs/demo/newton_test_scenario.py`
- **Integration Guide**: `NEWTON_INTEGRATION.md`
- **This Guide**: `docs/demo/COMPLETE_DEMO_GUIDE.md`

---

**Demo Environment Status**: ✅ **READY FOR TESTING**

The sales agent environment is fully configured with realistic products, campaign briefs, and automated delivery simulation. Newton can now act as a media buyer across three publishers (ESPN, CNN, NYT) using the AdCP protocol.


