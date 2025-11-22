# Newton AdCP Workflow Integration

## Overview
A complete workflow has been created for Newton to guide users through AdCP media buying operations using the three demo sales agents (ESPN, CNN, NYT).

## What Was Created

### 1. **Main Workflow File**
📄 **Location**: `/Users/danfinkel/github/newton/nri-server/newton/CONTAINER/workflows/public/adcp_media_buying/WORKFLOW.md`

**Purpose**: Comprehensive step-by-step guide for buying ads via AdCP

**Sections**:
- **Overview**: What AdCP is and what Newton can do
- **Connected Sales Agents**: The 3 demo agents (ESPN, CNN, NYT)
- **Recommended Workflow**: 4-step process:
  1. **Discovery**: Find available products using `get_products`
  2. **Creative Sync**: Register creatives using `sync_creatives`
  3. **Media Buy Creation**: Book campaigns using `create_media_buy`
  4. **Delivery Tracking**: Monitor performance using `get_media_buy_delivery`
- **Common Campaign Scenarios**: Brand awareness, targeted campaigns, multi-format tests
- **Troubleshooting**: Solutions for common errors
- **Workflow Completion Checklist**: What should be delivered to the user

### 2. **Quick Reference Guide**
📄 **Location**: `/Users/danfinkel/github/newton/nri-server/newton/CONTAINER/workflows/public/adcp_media_buying/QUICK_REFERENCE.md`

**Purpose**: Fast lookup for common operations

**Includes**:
- 4-step quick start with code examples
- Standard IAB creative format reference table
- Sales agents configuration table
- Budget calculator formulas
- Common errors & fixes table
- Campaign workflow checklist
- Pro tips for optimization

### 3. **Workflow Registration**
📄 **Location**: `/Users/danfinkel/github/newton/nri-server/newton/CONTAINER/workflows/public/WORKFLOW.md` (updated)

**Changes**:
- Added AdCP workflow to matching criteria
- Added path mapping: `"AdCP Media Buying Workflow" → adcp_media_buying`
- Added semantic patterns: "buy ads", "create media buy", "AdCP"

## How Newton Uses This Workflow

### Workflow Trigger
When a user says something like:
- "I want to buy some ads"
- "Create a media campaign"
- "How do I use AdCP?"
- "Buy advertising on ESPN"

Newton will:
1. **Detect workflow match** based on keywords
2. **Present workflow card** to the user with "Run Workflow" button
3. **Load workflow** when user clicks the button
4. **Follow the 4-step process** guided by the workflow instructions

### Workflow Steps (As Newton Executes Them)

#### Step 1: Discovery
```python
# Newton calls get_products on each sales agent
espn_products = mcp_24_get_products(brief="sports, basketball, Nike audience")
cnn_products = mcp_25_get_products(brief="news, family, holiday campaigns")
nyt_products = mcp_26_get_products(brief="premium, tech, affluent audience")

# Newton presents products to user for selection
```

#### Step 2: Creative Sync
```python
# Newton syncs creatives for selected campaigns
nike_creatives = [{
    "creative_id": "nike_air_jordan_728x90",
    "name": "Nike Air Jordan - Leaderboard",
    "format_id": "display_728x90",
    "click_through_url": "https://nike.com/air-jordan",
    "preview_url": "https://placeholder.com/nike_728x90.jpg",
    "assets": {"image": {"url": "https://placeholder.com/nike_728x90.jpg", "width": 728, "height": 90}}
}]

mcp_24_sync_creatives(creatives=nike_creatives)
```

#### Step 3: Media Buy Creation
```python
# Newton creates media buy campaign
nike_campaign = mcp_24_create_media_buy(
    product_ref="espn_homepage_leaderboard",  # From Step 1
    promoted_offering="Nike Air Jordan",
    packages=[{
        "package_id": "nike_espn_dec_2024",
        "creative_ids": ["nike_air_jordan_728x90"],  # From Step 2
        "start_date": "2024-12-01",
        "end_date": "2024-12-31",
        "pricing": {"model": "cpm", "amount": 25.0, "currency": "USD"},
        "guaranteed_impressions": 2000000,
        "pacing": "even"
    }]
)
```

#### Step 4: Delivery Tracking
```python
# Newton checks campaign delivery
delivery = mcp_24_get_media_buy_delivery(
    media_buy_ids=["nike_espn_dec_2024"]
)

# Newton presents delivery metrics to user
```

## Key Features of the Workflow

### ✅ Complete End-to-End Process
The workflow covers the entire media buying lifecycle from discovery to delivery tracking.

### ✅ Handles Known Issues
The workflow includes workarounds for known issues:
- **Creative format discovery**: Uses standard IAB format IDs directly instead of querying `list_creative_formats`
- **Creative sync requirement**: Explicitly requires syncing before creating media buys
- **Pacing field**: Specifies "even" or "asap" (required field that Newton discovered)

### ✅ Real Code Examples
Every step includes working Python code using the actual MCP tool names that Newton will discover.

### ✅ Error Handling
Comprehensive troubleshooting section with causes and fixes for common errors.

### ✅ Campaign Scenarios
Includes 3 common scenarios with complete workflows:
- Brand awareness (multi-publisher)
- Targeted campaign (single publisher)
- Multi-format testing

## Testing the Workflow

### For Newton Users
1. **Trigger the workflow**:
   ```
   User: "I want to buy ads for Nike on ESPN"
   ```

2. **Newton presents workflow card** with "Run Workflow" button

3. **User clicks button** → Newton loads the workflow

4. **Newton follows steps**:
   - Calls `get_products` to discover ESPN inventory
   - Asks user to confirm product selection
   - Syncs Nike creatives
   - Creates media buy
   - Shows delivery status

### For Developers
1. **Verify workflow file exists**:
   ```bash
   ls /Users/danfinkel/github/newton/nri-server/newton/CONTAINER/workflows/public/adcp_media_buying/
   ```

2. **Check Newton recognizes it**:
   - User asks: "what workflows do you have?"
   - Newton should list "AdCP Media Buying Workflow"

3. **Test end-to-end**:
   - Use Nike/ESPN campaign brief from `docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`
   - Verify all 4 steps complete successfully

## Demo Campaign Briefs

The workflow is designed to work with the demo campaign briefs in:
📄 `/Users/danfinkel/github/opensource/salesagent/docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`

**Campaigns**:
1. **Nike Air Jordan** → ESPN Sales Agent
   - Budget: $50,000
   - Audience: Sports enthusiasts, basketball fans
   - Formats: Display ads (728x90, 300x250)

2. **Coca-Cola Holiday** → CNN Sales Agent
   - Budget: $75,000
   - Audience: Family, national, holiday shoppers
   - Formats: Display ads (728x90, 970x250, 160x600)

3. **Apple Vision Pro** → NYT Sales Agent
   - Budget: $100,000
   - Audience: Affluent, tech-savvy professionals
   - Formats: Display ads (970x250, 300x250, 728x90)

## Sales Agent URLs

The workflow uses these sales agent MCP servers:

| Publisher | MCP Server URL | Port | Demo Advertiser |
|-----------|---------------|------|-----------------|
| ESPN | http://localhost:9580/mcp/ | 9580 | Nike |
| CNN | http://localhost:9581/mcp/ | 9581 | Coca-Cola |
| NYT | http://localhost:9582/mcp/ | 9582 | Apple |

**Authentication**: Disabled (test mode enabled via `ADCP_TESTING=true`)

## Workflow Benefits

### For Users
- **Guided Process**: Step-by-step instructions eliminate guesswork
- **Error Prevention**: Built-in checks and validation
- **Best Practices**: Follows AdCP protocol standards
- **Context Preserved**: Newton maintains campaign context throughout

### For Newton
- **Structured Execution**: Clear workflow reduces ambiguity
- **Tool Discovery**: MCP tools are discovered automatically
- **Error Recovery**: Troubleshooting guide helps Newton handle issues
- **Reusable Pattern**: Workflow can be applied to any AdCP-compliant sales agent

## Next Steps

### To Use the Workflow
1. ✅ Sales agents are running (`./scripts/demo/start_demo_agents.sh`)
2. ✅ Workflow files are in place (done)
3. ✅ Newton's MCP connectors are configured (see `NEWTON_INTEGRATION.md`)
4. 🔄 User triggers workflow: "I want to buy ads"
5. 🔄 Newton loads workflow and executes steps

### To Extend the Workflow
The workflow can be extended with additional capabilities:
- **Budget Optimization**: Automatically allocate budget across publishers
- **Performance Analysis**: Compare delivery across campaigns
- **Creative Testing**: A/B test creative variations
- **Reporting**: Generate wrap reports after campaigns complete

## Troubleshooting

### Workflow Not Triggering
**Issue**: User asks about ads but workflow doesn't load  
**Fix**: Check that Newton's workflow matching includes AdCP keywords

### MCP Tools Not Found
**Issue**: Newton can't find `get_products`, `sync_creatives`, etc.  
**Fix**: Verify MCP connectors are configured and sales agents are running

### Media Buy Creation Fails
**Issue**: `create_media_buy` returns error  
**Fix**: Follow workflow checklist - ensure creatives are synced first

### No Products Returned
**Issue**: `get_products` returns empty list  
**Fix**: Verify database is populated (`docker-compose -f docker-compose.testing.yml exec postgres psql -U adcp_user -d adcp -c "SELECT COUNT(*) FROM products;"`)

## Support

For questions or issues with the workflow:
1. **Review workflow**: `/Users/danfinkel/github/newton/nri-server/newton/CONTAINER/workflows/public/adcp_media_buying/WORKFLOW.md`
2. **Check quick reference**: `QUICK_REFERENCE.md` (same directory)
3. **Review sales agent docs**: `NEWTON_INTEGRATION.md`, `TESTING_NO_AUTH.md`
4. **Check database**: Run health checks in `./scripts/demo/start_demo_agents.sh`

---

**Created**: 2024-11-19  
**Updated**: 2024-11-19  
**Version**: 1.3  
**Status**: ✅ Ready for testing

## Recent Updates

### Version 1.4 (2024-11-19) ⭐ **CRITICAL BUG FIX**
- **Fixed**: Variable scoping bug causing misleading error messages
- **Issue**: `create_media_buy` returned `'Package' object has no attribute 'get'` error BUT campaign was actually created successfully
- **Symptom**: Newton confused - first call "fails" but campaign exists, retry gets "duplicate" error
- **Root Cause**: Two variable scoping bugs in pending approval code path:
  1. Used `pkg_data["package_id"]` from wrong loop scope (should be `pkg_obj.package_id`)
  2. Uninitialized `pricing_info_for_package` and `budget_value` variables
- **Solution**: Fixed variable initialization and scope in `src/core/tools/media_buy_create.py`
- **Impact**: `create_media_buy` now returns correct success/error status - Newton no longer confused! 🎉
- **See**: `NEWTON_SCOPING_BUG_FIX.md` for detailed technical analysis

### Version 1.3 (2024-11-19)
- **Fixed**: Increased Mock Adapter limits for realistic testing
- **Issue**: Newton hit inventory limits (1M impressions per package was too restrictive)
- **Solution**: Updated `src/adapters/mock_ad_server.py` to increase limits:
  - Impressions per package: **1M → 10M** (per package)
  - Total campaign budget: **$1M → $10M**
- **Impact**: Newton can now book campaigns with realistic impression goals

### Version 1.2 (2024-11-19)
- **Fixed**: Added `PricingOption` records for all products
- **Issue**: Data integrity error - products had no pricing options configured
- **Solution**: Updated `start_demo_agents.sh` to create pricing options for all 9 products
- **Details**: 
  - ESPN: $15-25 CPM (homepage, sidebar, mobile)
  - CNN: $28-35 CPM (homepage, article, breaking news)
  - NYT: $35-40 CPM (homepage, article, opinion)
- **Impact**: Newton can now successfully create media buys with valid pricing

### Version 1.1 (2024-11-19)
- **Fixed**: Added `AuthorizedProperty` creation to database setup
- **Issue**: Setup checklist validation was blocking media buy creation
- **Solution**: Updated `start_demo_agents.sh` to create authorized properties for each tenant
- **Impact**: Newton can now successfully create media buys without setup blockers

