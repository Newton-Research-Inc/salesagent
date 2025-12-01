# Newton + Yahoo DSP Demo Script

## 🎯 Demo Objective

Show Newton buying media through **Yahoo DSP (programmatic)** vs **ESPN (direct publisher)**, highlighting:
1. **Audience targeting** (DSP) vs placement targeting (publisher)
2. **Auction-based pricing** (DSP) vs fixed pricing (publisher)
3. **Rich performance metrics** (DSP) vs basic metrics (publisher)
4. **Strategic decision-making** by Newton

---

## 📋 Demo Scenario

**Campaign Goal:** Nike wants to launch a new Air Jordan sneaker to sneaker enthusiasts with a $50K budget.

**Newton's Task:** 
- Evaluate direct (ESPN) vs programmatic (Yahoo DSP) options
- Choose the best strategy
- Execute the buy
- Compare performance

---

## 🎬 Demo Script

### **Act 1: Discovery Phase**

Newton explores available inventory across both channels.

```python
# Newton's internal reasoning:
"I need to find the best inventory for Nike Air Jordan launch.
Let me check both direct publisher inventory (ESPN) and 
programmatic options (Yahoo DSP)."

# Tool calls:
mcp_espn.get_products(brief="Display advertising for sneaker launch")
mcp_yahoo.get_products(brief="Audience-targeted display for sneaker enthusiasts")
```

**Expected Results:**

**ESPN (Direct):**
```json
{
  "products": [
    {
      "product_id": "espn_display_728x90",
      "name": "ESPN Homepage Banner",
      "description": "Premium leaderboard placement on ESPN homepage",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 5.00,
        "currency": "USD",
        "is_fixed": true  // ← Fixed rate
      }],
      "targeting_template": {},  // ← No audience targeting
      "delivery_type": "guaranteed"
    }
  ]
}
```

**Yahoo DSP (Programmatic):**
```json
{
  "products": [
    {
      "product_id": "yahoo_display_728x90",
      "name": "Audience-Targeted Display",
      "description": "Reach high-value audiences across Yahoo Exchange + open web",
      "pricing_options": [{
        "pricing_model": "CPM",
        "rate": 6.50,
        "currency": "USD",
        "is_fixed": false,  // ← Auction-based
        "price_guidance": {
          "floor": 5.00,
          "p50": 6.50,
          "p75": 8.00
        }
      }],
      "targeting_template": {
        "audiences_any_of": ["auto_intenders", "fitness_enthusiasts", "high_income_households"]
      },
      "delivery_type": "programmatic"
    }
  ]
}
```

**Newton's Analysis:**
```
ESPN: 
- ✅ Lower CPM ($5.00 fixed)
- ✅ Guaranteed delivery
- ✅ Premium sports context (ESPN homepage)
- ❌ No audience targeting (reaches ALL ESPN visitors)
- ❌ Higher waste (many non-sneaker-enthusiasts)

Yahoo DSP:
- ✅ Audience targeting (auto_intenders + fitness_enthusiasts)
- ✅ Broader reach (100+ sites, not just ESPN)
- ✅ Performance optimization (auto-bidding)
- ❌ Higher CPM ($6.50, +30%)
- ❌ Non-guaranteed delivery
- ❌ Requires campaign approval

DECISION: Split budget - $25K ESPN (guaranteed reach) + $25K Yahoo DSP (targeted reach)
RATIONALE: Diversification + test audience targeting value
```

---

### **Act 2: Campaign Execution**

Newton executes buys on both platforms simultaneously.

#### **ESPN Buy (Direct/Simple)**

```python
mcp_espn.sync_creatives(
    creatives=[
        {
            "creative_id": "nike_aj_728x90",
            "name": "Nike Air Jordan - Leaderboard",
            "format_id": "display_728x90",
            "click_through_url": "https://nike.com/airjordan",
            "preview_url": "https://assets.nike.com/aj_728x90.jpg",
            "assets": {
                "image": {
                    "url": "https://assets.nike.com/aj_728x90.jpg",
                    "width": 728,
                    "height": 90
                }
            }
        }
    ]
)

mcp_espn.create_media_buy(
    buyer_ref="nike_aj_espn_q4_2025",
    brand_manifest={
        "name": "Nike",
        "url": "https://nike.com"
    },
    start_time="2025-12-01T00:00:00Z",
    end_time="2025-12-31T23:59:59Z",
    packages=[{
        "package_id": "espn_homepage_728x90",
        "product_id": "espn_display_728x90",
        "budget": 25000,
        "impressions": 5000000,  # 5M impressions at $5 CPM
        "creative_ids": ["nike_aj_728x90"],
        "pacing": "even"
    }]
)
```

**ESPN Response:**
```json
{
  "status": "active",  // ← Immediate activation
  "media_buy_id": "mock_espn_12345",
  "packages": [{
    "package_id": "espn_homepage_728x90",
    "status": "delivering",
    "external_id": "espn_order_98765"
  }]
}
```

**Newton's Observation:** "ESPN campaign activated immediately. Guaranteed delivery started."

---

#### **Yahoo DSP Buy (Programmatic/Complex)**

```python
mcp_yahoo.sync_creatives(
    creatives=[
        {
            "creative_id": "nike_aj_dsp_728x90",
            "name": "Nike Air Jordan - DSP Leaderboard",
            "format_id": "display_728x90",
            "click_through_url": "https://nike.com/airjordan",
            "preview_url": "https://assets.nike.com/aj_728x90.jpg",
            "assets": {
                "image": {
                    "url": "https://assets.nike.com/aj_728x90.jpg",
                    "width": 728,
                    "height": 90
                }
            }
        }
    ]
)

mcp_yahoo.create_media_buy(
    buyer_ref="nike_aj_yahoo_dsp_q4_2025",
    brand_manifest={
        "name": "Nike",
        "url": "https://nike.com"
    },
    start_time="2025-12-01T00:00:00Z",
    end_time="2025-12-31T23:59:59Z",
    packages=[{
        "package_id": "yahoo_dsp_audience_728x90",
        "product_id": "yahoo_display_728x90",
        "budget": 25000,
        "creative_ids": ["nike_aj_dsp_728x90"],
        "pacing": "even",
        # DSP-specific targeting
        "targeting_overlay": {
            "audiences_any_of": [
                "auto_intenders",
                "fitness_enthusiasts", 
                "high_income_households"
            ],
            "geo_country_any_of": ["US"]
        }
    }]
)
```

**Yahoo DSP Response:**
```json
{
  "status": "pending_review",  // ← Requires approval (DSP behavior)
  "media_buy_id": "yahoo_dsp_abc123def456",
  "packages": [{
    "package_id": "yahoo_dsp_audience_728x90",
    "status": "pending",
    "external_id": "yahoo_adgroup_xyz789"
  }],
  
  // DSP-specific response fields:
  "bid_landscape": {
    "median_winning_bid": 6.83,
    "percentile_25": 5.20,
    "percentile_75": 8.13,
    "competition_level": "medium",
    "estimated_win_rate_at_bid": {
      "6.50": 0.45  // 45% win rate at our bid
    }
  },
  "estimated_reach": {
    "estimated_unique_users": 2500000,
    "estimated_impressions": 3846154,  // ~3.8M impressions at $6.50 CPM
    "confidence": 0.85
  }
}
```

**Newton's Observation:** 
```
"Yahoo DSP campaign pending review. 
Estimated reach: 2.5M users (vs ESPN's 5M impressions).
Bid landscape shows competitive environment:
- Median winning bid: $6.83 (our bid: $6.50)
- Estimated win rate: 45%
- Competition: Medium

Yahoo DSP provides more data upfront, but requires approval delay.
ESPN is simpler and immediate."
```

---

### **Act 3: Performance Monitoring**

Newton checks performance after 1 week. This is where DSP really shines.

#### **ESPN Performance (Basic Metrics)**

```python
mcp_espn.get_media_buy_delivery(
    media_buy_id="mock_espn_12345",
    start_date="2025-12-01",
    end_date="2025-12-07"
)
```

**ESPN Response:**
```json
{
  "packages": [{
    "package_id": "espn_homepage_728x90",
    "status": "delivering",
    "impressions": 1250000,  // 1.25M of 5M (25% through)
    "spend": 6250.00,  // $6,250 of $25K
    "avg_cpm": 5.00
  }],
  "totals": {
    "impressions": 1250000,
    "spend": 6250.00
  }
}
```

**Newton's Analysis:** "ESPN on track. 25% delivered. Basic metrics only."

---

#### **Yahoo DSP Performance (Rich Metrics)**

```python
mcp_yahoo.get_media_buy_delivery(
    media_buy_id="yahoo_dsp_abc123def456",
    start_date="2025-12-01",
    end_date="2025-12-07"
)
```

**Yahoo DSP Response:**
```json
{
  "packages": [{
    "package_id": "yahoo_dsp_audience_728x90",
    "status": "delivering",
    
    // Standard metrics:
    "impressions": 962500,  // ~963K impressions
    "clicks": 1060,  // Click data!
    "spend": 6256.25,
    "avg_cpm": 6.50,
    
    // DSP-specific metrics:
    "metadata": {
      "bid_requests": 3125000,  // Total auction opportunities
      "win_rate": 0.308,  // Won 30.8% of auctions
      "avg_bid": 6.50,
      "avg_win_price": 6.51,  // Actually paid $6.51 CPM
      
      "viewability_rate": 0.74,  // 74% viewable impressions
      "ctr": 0.0011,  // 0.11% click-through rate
      
      "conversions": 24,  // Post-click conversions!
      "conversion_rate": 0.0226,  // 2.26% of clicks converted
      
      "audience_segments": 3  // Targeting 3 segments
    }
  }],
  "totals": {
    "impressions": 962500,
    "clicks": 1060,
    "spend": 6256.25
  }
}
```

**Newton's Deep Analysis:**
```
ESPN vs Yahoo DSP Performance (Week 1):

REACH:
- ESPN: 1.25M impressions (broader, less targeted)
- Yahoo DSP: 963K impressions (lower, but more relevant)

EFFICIENCY:
- ESPN: Unknown clicks/conversions
- Yahoo DSP: 
  - 1,060 clicks (0.11% CTR)
  - 24 conversions (2.26% conversion rate)
  - Won 30.8% of 3.1M auction opportunities
  - 74% viewability (high quality impressions)

COST EFFICIENCY:
- ESPN: $5.00 CPM (cost per impression)
- Yahoo DSP: $6.51 CPM, BUT...
  - Cost per click: $5.90 ($6,256 / 1,060 clicks)
  - Cost per conversion: $260.68 ($6,256 / 24 conversions)
  
INSIGHT: Yahoo DSP's higher CPM is justified by:
1. Audience targeting → Better conversion rate
2. Performance tracking → Can optimize
3. Viewability data → Higher quality impressions

RECOMMENDATION: 
- Continue both campaigns
- Consider shifting more budget to Yahoo DSP if conversion tracking 
  shows positive ROI vs ESPN (which we can't measure)
```

---

### **Act 4: Optimization Decision**

Based on Week 1 data, Newton makes strategic recommendations.

**Newton's Strategic Report:**

```markdown
# Nike Air Jordan Campaign Analysis - Week 1

## Campaign Overview
- Total Budget: $50,000 ($25K ESPN + $25K Yahoo DSP)
- Week 1 Spend: $12,506 (25% of budget)
- Remaining: $37,494

## Channel Performance

### ESPN (Direct Publisher)
- Impressions: 1.25M
- Spend: $6,250
- CPM: $5.00 (fixed)
- Metrics: Basic (impressions only)
- Status: On track, predictable

### Yahoo DSP (Programmatic)
- Impressions: 963K
- Clicks: 1,060
- Conversions: 24
- Spend: $6,256
- CPM: $6.51 (auction, slightly above bid)
- Win Rate: 30.8%
- Viewability: 74%
- CTR: 0.11%
- Conversion Rate: 2.26%

## Key Insights

1. **Audience Targeting Value**
   - Yahoo DSP delivers 23% fewer impressions BUT...
   - Generates measurable clicks (1,060) and conversions (24)
   - ESPN clicks/conversions = unknown

2. **Cost Per Acquisition**
   - Yahoo DSP: $260.68 per conversion
   - ESPN: Cannot calculate (no conversion data)
   
3. **Quality Over Quantity**
   - Yahoo DSP: 74% viewability (high quality)
   - ESPN: Viewability unknown

## Strategic Recommendation

### Option A: Stay the Course (Current 50/50 Split)
- Pros: Diversification, testing both channels
- Cons: May not optimize budget allocation

### Option B: Shift Budget to Yahoo DSP (70/30)
- Reasoning: Proven conversion tracking + optimization
- New allocation: $35K Yahoo DSP, $15K ESPN
- Expected: 2-3x more conversions, better ROI measurement

### Option C: Request ESPN Conversion Tracking
- Install Nike pixel on click-through landing page
- Compare true ESPN conversion rate to Yahoo DSP
- Make data-driven decision in Week 2

## Recommended Action: Option C + Option B
1. Implement conversion tracking for ESPN (Week 2)
2. Shift budget 70/30 to Yahoo DSP immediately
3. Re-evaluate in Week 3 with complete data

## Expected Outcomes
- Yahoo DSP: ~72 conversions (vs 24 in Week 1)
- ESPN: Conversion data available for comparison
- Total campaign: Better ROI visibility
```

---

## 🎭 Demo Flow Summary

### **What Newton Demonstrates:**

1. **Multi-Channel Discovery**
   - Queries both direct (ESPN) and programmatic (Yahoo DSP)
   - Compares options objectively

2. **Strategic Decision-Making**
   - Identifies trade-offs (guaranteed vs targeted)
   - Chooses diversification strategy (split budget)

3. **Execution Across Platforms**
   - Handles immediate activation (ESPN)
   - Manages approval delays (Yahoo DSP)

4. **Performance Analysis**
   - Interprets basic metrics (ESPN)
   - Leverages rich DSP data (Yahoo DSP)

5. **Data-Driven Optimization**
   - Identifies Yahoo DSP's superior measurement
   - Recommends budget reallocation
   - Proposes A/B testing

---

## 💡 Key Demo Talking Points

### **For Audience:**

1. **"Newton understands trade-offs"**
   - Lower CPM (ESPN) vs better targeting (Yahoo DSP)
   - Guaranteed delivery vs performance optimization

2. **"Newton leverages programmatic advantages"**
   - Audience targeting (fitness enthusiasts, auto-intenders)
   - Real-time bidding (auction participation)
   - Rich analytics (viewability, conversions, win rates)

3. **"Newton makes strategic decisions"**
   - Diversifies across channels
   - Shifts budget based on performance
   - Requests additional tracking for better decisions

4. **"AdCP protocol enables all of this"**
   - Same tools (`get_products`, `create_media_buy`) work across channels
   - Newton doesn't need to know implementation details
   - Publisher vs DSP differences are abstracted

---

## 🚀 Running the Demo

### **Setup (Before Demo):**

1. Ensure all 4 services running:
   ```bash
   aws ecs describe-services --cluster salesagent-espn --services salesagent-espn --region us-east-1
   aws ecs describe-services --cluster salesagent-yahoo --services salesagent-yahoo --region us-east-1
   ```

2. Verify Newton has MCP servers registered:
   - `mcp_espn` → `http://espn.salesagent.local:9580/mcp`
   - `mcp_yahoo` → `http://yahoo.salesagent.local:9580/mcp`

3. Clean previous demo data (optional):
   ```python
   mcp_espn.clean_demo_data(tenant_id="espn")
   mcp_yahoo.clean_demo_data(tenant_id="yahoo")
   ```

### **Demo Execution:**

Run Newton with the scenario prompt:

```
PROMPT: "I'm planning a Nike Air Jordan sneaker launch campaign with a $50K 
budget. I want to reach sneaker enthusiasts and fitness-minded consumers. 
Compare options across ESPN (direct publisher) and Yahoo DSP (programmatic), 
then execute the best strategy. After 1 week, analyze performance and recommend 
optimizations."
```

Newton will:
1. Call `get_products` on both servers
2. Compare options
3. Execute `sync_creatives` + `create_media_buy` on both
4. Call `get_media_buy_delivery` after simulated delay
5. Generate strategic analysis
6. Recommend next steps

---

## 📊 Expected Demo Outcomes

### **Audience Takeaways:**

1. ✅ **Newton can intelligently compare channels**
   - Understands direct vs programmatic trade-offs
   
2. ✅ **AdCP protocol is flexible**
   - Same tools work for both publisher and DSP
   
3. ✅ **Yahoo DSP adds value**
   - Audience targeting
   - Rich performance data
   - Conversion tracking
   
4. ✅ **Newton makes data-driven decisions**
   - Not just executing orders
   - Analyzing, optimizing, recommending

---

## 🎬 Alternative Demo Scenarios

### **Scenario 2: "Pure Programmatic" (Yahoo DSP Only)**
- Focus: Deep dive into DSP features
- Showcase: Audience segments, bid optimization, win rates
- Best for: Programmatic advertising experts

### **Scenario 3: "Budget Optimization" (Multi-Round)**
- Start: $10K test on both channels
- Round 2: Reallocate based on Week 1 performance
- Round 3: Final optimization
- Best for: Performance marketing audience

### **Scenario 4: "Cross-Channel Attribution" (Advanced)**
- ESPN: Upper funnel awareness
- Yahoo DSP: Lower funnel conversion
- Analyze: How ESPN impressions assist Yahoo DSP conversions
- Best for: Advanced marketing strategists

---

## 📝 Demo Script Notes

**Preparation time:** 5 minutes
**Demo duration:** 10-15 minutes (live)
**Technical level:** Medium (assumes AdCP knowledge)

**Props needed:**
- Newton UI or CLI
- AWS console (show ECS services)
- Logs (optional, show real-time)

**Backup plan:** Pre-recorded responses if live demo fails

---

This demo script effectively shows Yahoo DSP's unique value while demonstrating Newton's strategic capabilities! 🚀

