# Newton + AdCP Sales Agent Demo Summary

## 🎯 What We Built

A complete end-to-end demonstration of an AI agent (Newton) acting as a **media buyer**, purchasing advertising inventory from multiple publishers (ESPN, CNN, NYT) via the **Advertising Context Protocol (AdCP)** over **Model Context Protocol (MCP)**.

---

## 🤖 What Newton Does (The Buyer Agent)

**Newton is an AI-powered media buying agent** that:

1. **Discovers Inventory**
   - Connects to multiple AdCP sales agents (ESPN, CNN, NYT) via MCP
   - Calls `get_products` to find available advertising inventory
   - Parses structured product data (formats, targeting, pricing)

2. **Manages Creative Assets**
   - Calls `sync_creatives` to register creative assets (images, videos)
   - Provides creative specifications (dimensions, URLs, format IDs)
   - Handles creative validation and format compliance

3. **Creates Media Buys**
   - Calls `create_media_buy` with campaign details:
     - Budget allocation across packages
     - Start/end dates and pacing
     - Creative assignments per package
     - Targeting parameters
   - Receives `media_buy_id` for tracking

4. **Monitors Campaign Performance**
   - Calls `get_media_buy_delivery` to track metrics
   - Reviews impressions delivered, budget spent, delivery status
   - Makes optimization decisions based on performance

**Newton's Intelligence:**
- Interprets natural language campaign briefs (e.g., "Launch Nike Air Jordan to basketball fans")
- Translates business goals into technical AdCP parameters
- Manages multi-publisher campaigns across ESPN, CNN, NYT
- Handles budget allocation and impression forecasting

---

## 🏢 What The ESPN MCP Server Does (The Sales Agent)

**ESPN's Sales Agent is an AdCP-compliant server** that:

### 1. **Exposes Advertising Inventory via MCP**

**Tools Provided:**
- `get_products` - List available ad products with targeting and pricing
- `list_creative_formats` - Available creative formats (728x90, 300x250, etc.)
- `sync_creatives` - Register/update creative assets
- `list_creatives` - View registered creatives
- `create_media_buy` - Book advertising campaigns
- `update_media_buy` - Modify existing campaigns
- `get_media_buy_delivery` - Track campaign performance
- `get_signals` - Available audience/contextual signals
- `activate_signal` - Enable targeting signals
- `list_authorized_properties` - Properties the agent can represent

### 2. **Manages Campaign Lifecycle**

**Campaign Creation:**
- Validates creative formats and dimensions
- Checks product availability and pricing
- Creates orders and line items in ad server (Mock/GAM/Kevel)
- Assigns creatives to packages
- Sets targeting parameters

**Campaign Execution:**
- Simulates ad delivery (Mock adapter)
- Tracks impressions, clicks, spend
- Generates delivery reports
- Handles pacing (even/front-loaded)

**Campaign Updates:**
- Budget modifications
- Creative swaps
- Date changes
- Status updates (pause/resume)

### 3. **Multi-Adapter Architecture**

**Supported Ad Servers:**
- **Mock Adapter** (Demo) - Simulates ad server behavior, no real infrastructure
- **Google Ad Manager (GAM)** - Production integration via GAM API
- **Kevel** - Programmatic ad server integration
- **Triton Digital** - Audio/podcast advertising integration

**Adapter Pattern Benefits:**
- Publishers choose their ad server
- Consistent AdCP interface regardless of backend
- Easy to add new ad server integrations

---

## 🏗️ Demo Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEWTON (Buyer)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Momentum Agent (AI-powered media buying workflow)      │   │
│  │  - Interprets campaign briefs                           │   │
│  │  - Discovers products from multiple publishers          │   │
│  │  - Manages creative assets                              │   │
│  │  - Creates and monitors campaigns                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              │ MCP Client                        │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               │ HTTP + Server-Sent Events (SSE)
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  ESPN Agent   │     │  CNN Agent    │     │  NYT Agent    │
│  (port 9580)  │     │  (port 9581)  │     │  (port 9582)  │
├───────────────┤     ├───────────────┤     ├───────────────┤
│ MCP Server    │     │ MCP Server    │     │ MCP Server    │
│ ↓             │     │ ↓             │     │ ↓             │
│ AdCP Tools    │     │ AdCP Tools    │     │ AdCP Tools    │
│ ↓             │     │ ↓             │     │ ↓             │
│ Mock Adapter  │     │ Mock Adapter  │     │ Mock Adapter  │
│ ↓             │     │ ↓             │     │ ↓             │
│ PostgreSQL    │     │ PostgreSQL    │     │ PostgreSQL    │
│ (shared DB)   │     │ (shared DB)   │     │ (shared DB)   │
└───────────────┘     └───────────────┘     └───────────────┘
```

---

## 📊 Demo Data Setup

### **3 Publishers (Sales Agents)**

| Publisher | URL | Token | Products | Advertiser |
|-----------|-----|-------|----------|------------|
| **ESPN** | http://localhost:9580/mcp/ | `espn_test_token` | 3 (Homepage, Live Game, Mobile) | Nike |
| **CNN** | http://localhost:9581/mcp/ | `cnn_test_token` | 3 (Homepage, Article, Breaking News) | Coca-Cola |
| **NYT** | http://localhost:9582/mcp/ | `nyt_test_token` | 3 (Homepage, Article, Opinion) | Apple |

### **Product Examples**

**ESPN Homepage Leaderboard:**
- Format: 728x90 display banner
- Placement: ESPN.com homepage above the fold
- Targeting: Sports enthusiasts, NBA fans
- Pricing: $25 CPM (fixed)
- Impressions: Up to 10M per month

**CNN Breaking News Banner:**
- Format: 970x250 display banner
- Placement: CNN.com breaking news section
- Targeting: News consumers, current events
- Pricing: $35 CPM (fixed)
- Impressions: Up to 10M per month

**NYT Homepage Billboard:**
- Format: 970x250 display banner
- Placement: NYTimes.com homepage hero position
- Targeting: Affluent readers, thought leaders
- Pricing: $40 CPM (fixed)
- Impressions: Up to 10M per month

---

## 🎬 Example Campaign Flow

### **Nike Air Jordan Q4 2025 Campaign**

**1. Newton receives campaign brief:**
> "Launch the new Air Jordan line to sports enthusiasts and basketball fans during Q4 2025 basketball season. Target: Adults 18-35, male-skewed, urban, basketball, sports, sneakers, NBA, US major metros. Budget: $50,000. Dec 1-31, 2025."

**2. Newton discovers products:**
```python
# Calls ESPN's MCP server
result = mcp_24_get_products(
    brief="Sports, basketball, NBA, male 18-35, urban, December 2025"
)
# Receives 3 matching products from ESPN
```

**3. Newton syncs creatives:**
```python
# Registers creative assets
result = mcp_24_sync_creatives(
    creatives=[
        {
            "creative_id": "nike_air_jordan_leaderboard",
            "format_id": "display_728x90",
            "assets": {"image": {"url": "...", "width": 728, "height": 90}},
            "click_through_url": "https://nike.com/airjordan"
        },
        # ... more creatives
    ]
)
```

**4. Newton creates media buy:**
```python
# Books the campaign
result = mcp_24_create_media_buy(
    buyer_ref="nike_air_jordan_q4_2025",
    brand_manifest={"name": "Nike", "url": "https://nike.com"},
    start_time="2025-12-01T00:00:00-05:00",
    end_time="2025-12-31T23:59:59-05:00",
    packages=[
        {
            "package_id": "nike_espn_homepage_leaderboard_dec2025",
            "product_id": "espn_homepage_leaderboard",
            "creative_ids": ["nike_air_jordan_leaderboard"],
            "budget": 20000.0,  # $20k package
            "impressions": 800000,  # 800k impressions
            "pacing": "even"
        },
        # ... more packages for live game and mobile
    ]
)
# Receives media_buy_id: "buy_abc123"
```

**5. Newton monitors performance:**
```python
# Checks delivery status
result = mcp_24_get_media_buy_delivery(
    media_buy_ids=["buy_abc123"]
)
# Receives impressions delivered, budget spent, delivery pacing
```

---

## 🐛 Bugs Fixed During Development

We encountered and fixed **4 critical bugs** during integration:

### **Bug #1: Variable Scoping (Pending Approval Path)**
- **Problem**: Wrong loop variable used, uninitialized variables
- **Impact**: Pending approval code path would fail
- **Fix**: Corrected variable scoping and initialization

### **Bug #2: Package Type Checking (Auto-Approval Path)**
- **Problem**: Called `.get()` on Pydantic Package object instead of dict
- **Impact**: `'Package' object has no attribute 'get'` error
- **Fix**: Added `isinstance()` check before calling `.get()`

### **Bug #3: Asset Field Name Mismatch**
- **Problem**: Mock adapter expected `asset["id"]` but code passed `asset["creative_id"]`
- **Impact**: `CREATIVE_UPLOAD_FAILED ... 'id'` error
- **Fix**: Added both `"id"` and `"creative_id"` fields to asset dict

### **Bug #4: SQLAlchemy Session Detachment (3 attempts!)**
- **Problem**: Accessing Creative ORM object attributes after session detachment
- **Impact**: `DetachedInstanceError: Instance <Creative> is not bound to a Session`
- **Attempt 1**: Load attributes before adapter call → ❌ Already detached
- **Attempt 2**: Eager load into dict after query → ❌ Still accessing ORM attributes
- **Attempt 3**: Use dict values exclusively → ✅ **Success!**
- **Fix**: Eager load all attributes into dict immediately after query, then use ONLY dict values

**Key Lesson**: SQLAlchemy lazy-loads attributes. When accessing ORM objects outside the session context (even in the same function!), they can become detached. **Always eager-load to plain Python dicts immediately after query.**

---

## 🚀 Next Improvements for the Demo

### **Phase 1: Enhanced Demo Experience** (Quick Wins)

1. **Campaign Success Visualization**
   - Add a simple web dashboard showing Newton's campaigns
   - Display: campaign status, budget spent, impressions delivered
   - URL: `http://localhost:9501/campaigns/newton` (add to admin UI)

2. **Multi-Publisher Workflow**
   - Newton creates campaigns across ESPN, CNN, and NYT simultaneously
   - Demonstrates cross-publisher budget allocation
   - Shows Newton managing 3 separate media buys in parallel

3. **Creative Optimization Workflow**
   - Newton syncs multiple creative variations per format
   - Tests A/B creative performance
   - Demonstrates `update_media_buy` for creative swaps

4. **Campaign Brief Library**
   - Add 10 realistic campaign briefs (Nike, Coca-Cola, Apple, etc.)
   - Each brief targets different publisher strengths
   - Newton can randomly select or user can choose

5. **Delivery Simulation Polish**
   - Mock adapter generates more realistic delivery curves
   - Add impression pacing variations (front-loaded, even, back-loaded)
   - Simulate delivery issues (under-delivery, over-delivery)

### **Phase 2: Advanced Features** (Medium Complexity)

6. **Signal Discovery & Activation**
   - Newton calls `get_signals` to discover targeting options
   - Activates contextual/audience signals via `activate_signal`
   - Demonstrates targeting customization

7. **Budget Optimization Loop**
   - Newton monitors `get_media_buy_delivery` throughout campaign
   - Calls `update_media_buy` to reallocate budget based on performance
   - Shows adaptive campaign management

8. **Multi-Format Campaign**
   - Newton creates campaigns with display + video + native formats
   - Each format has different creatives and pricing
   - Demonstrates format diversity

9. **Approval Workflow Demo**
   - Disable auto-approval for one publisher (e.g., NYT)
   - Newton creates media buy → goes to pending approval
   - Admin UI shows approval queue → approve manually
   - Newton receives approval notification

10. **Push Notifications (Webhooks)**
    - Newton registers webhook via `push_notification_config`
    - Sales agent sends delivery updates to Newton
    - Demonstrates real-time campaign monitoring

### **Phase 3: Production-Ready Features** (High Complexity)

11. **Real Ad Server Integration**
    - Connect ESPN agent to Google Ad Manager
    - Use GAM adapter instead of Mock adapter
    - Newton creates actual GAM orders/line items

12. **Multi-Tenant Newton**
    - Newton manages campaigns for multiple advertisers
    - Each advertiser has separate tokens and budgets
    - Demonstrates agent-as-a-service model

13. **Performance Analytics Dashboard**
    - Real-time charts showing:
      - Impressions over time
      - Budget pacing vs. delivery pacing
      - CTR and conversion metrics
    - Export reports as CSV/PDF

14. **Competitive Bidding Simulation**
    - Multiple Newton instances bid on same inventory
    - First-price or second-price auction mechanics
    - Demonstrates programmatic buying dynamics

15. **Natural Language Campaign Management**
    - Newton accepts plain English commands:
      - "Increase ESPN budget by 20%"
      - "Pause CNN campaign until next Monday"
      - "Show me top performing creatives"
    - Full conversational campaign management

---

## 🎓 What This Demo Proves

### **For Publishers:**
- ✅ AdCP enables AI agents to buy advertising autonomously
- ✅ Publishers expose inventory via simple MCP tools
- ✅ Backend flexibility (Mock, GAM, Kevel - same interface)
- ✅ Standard protocol reduces integration complexity

### **For Advertisers:**
- ✅ AI agents can manage multi-publisher campaigns
- ✅ Natural language briefs → technical media buys
- ✅ Automated creative management and optimization
- ✅ Real-time performance monitoring and adjustment

### **For The Industry:**
- ✅ AdCP + MCP enables a new paradigm: **AI-to-AI advertising**
- ✅ Reduces manual campaign setup from hours to seconds
- ✅ Enables sophisticated optimization strategies
- ✅ Opens door to autonomous media trading

---

## 📂 Key Files

**Setup Scripts:**
- `scripts/demo/start_demo_agents.sh` - Start all 3 sales agents + populate data
- `scripts/demo/stop_demo_agents.sh` - Stop all services cleanly
- `scripts/demo/clean_campaigns.sh` - Delete test campaigns

**Configuration:**
- `docker-compose.testing.yml` - 3 separate MCP servers (ESPN, CNN, NYT)
- `.env` - Port configuration and test mode settings

**Documentation:**
- `NEWTON_INTEGRATION.md` - Connection details for Newton
- `DEMO_SUMMARY.md` - This file
- `COMPLETE_SESSION_FIX.md` - Bug #4 detailed analysis

**Newton Workflows:**
- `newton/CONTAINER/workflows/public/adcp_media_buying/WORKFLOW.md` - Step-by-step workflow
- `newton/CONTAINER/workflows/public/adcp_media_buying/QUICK_REFERENCE.md` - Quick reference

---

## 🎯 Recommended Next Steps

**For immediate impact:**
1. ✅ **Multi-Publisher Campaign** - Have Newton create campaigns on ESPN, CNN, and NYT simultaneously
2. ✅ **Campaign Dashboard** - Build simple web view showing Newton's campaigns
3. ✅ **Creative A/B Testing** - Newton syncs multiple creatives and compares performance

**For showcase:**
4. ✅ **Signal Activation** - Demonstrate contextual/audience targeting
5. ✅ **Budget Optimization** - Show Newton reallocating budget based on performance
6. ✅ **Push Notifications** - Real-time delivery updates via webhooks

**For production:**
7. ✅ **GAM Integration** - Connect to real Google Ad Manager
8. ✅ **Performance Dashboard** - Real-time charts and analytics
9. ✅ **Multi-Tenant Newton** - Manage campaigns for multiple advertisers

---

## 🏆 Success Metrics

**What We Achieved:**
- ✅ Newton successfully discovers products from 3 publishers
- ✅ Newton syncs creative assets with proper format validation
- ✅ Newton creates media buys with budget, targeting, and pacing
- ✅ Sales agents manage campaign lifecycle (create, track, update)
- ✅ Mock adapter simulates realistic ad delivery
- ✅ Complete end-to-end AI-powered media buying workflow

**Demo Readiness:**
- ✅ One-command setup: `./scripts/demo/start_demo_agents.sh`
- ✅ Clean slate: `./scripts/demo/clean_campaigns.sh`
- ✅ No authentication required (test mode)
- ✅ Realistic product catalog (ESPN, CNN, NYT)
- ✅ Documented workflows for Newton

---

**Status**: ✅ **DEMO READY - Newton can autonomously buy advertising across multiple publishers!** 🎉

