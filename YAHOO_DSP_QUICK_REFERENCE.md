# Yahoo DSP - Quick Reference Card

## 🎯 What is Yahoo DSP?

A **Demand-Side Platform (DSP)** sales agent that simulates **programmatic advertising** alongside your direct publisher agents (ESPN, CNN, NYT).

---

## 📊 Direct vs Programmatic Comparison

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

### 2. Premium Display + Retargeting (300x250)
- **CPM:** $8.00 (bid-based)
- **Focus:** Site retargeting pools
- **Use Case:** Abandoned cart recovery, conversion optimization

### 3. Mobile Audience Network (320x50)
- **CPM:** $5.50 (bid-based)
- **Focus:** Mobile behavioral targeting
- **Use Case:** Mobile-first campaigns, app installs

---

## 🎬 Demo Scenarios

### Scenario 1: Direct vs Programmatic
```
Nike needs $50K in display ads

ESPN (Direct):
→ $5.00 CPM × 10M impressions = $50K
→ Guaranteed delivery
→ ESPN homepage only

Yahoo DSP (Programmatic):
→ $6.50 CPM × ~7.7M impressions = $50K
→ Non-guaranteed (auction-based)
→ Across 100+ sites with audience targeting
→ Auto-optimization

Decision: Split budget to compare!
```

### Scenario 2: Audience Targeting
```
Nike Air Jordan launch

ESPN: All ESPN visitors (no filtering)
Yahoo DSP: auto_intenders + fitness_enthusiasts + high_income
→ Higher relevance → Better conversions
```

### Scenario 3: Performance Optimization
```
Goal: Maximize clicks for $50K

Yahoo DSP Auto-Bidding:
- Mobile: +20% (better CTR)
- Evening: +15% (higher engagement)
- Weekend: -10% (lower competition)
→ 5% more clicks than manual
```

---

## 🚀 Quick Deploy

```bash
# 1. Build & Push
docker build -t salesagent:yahoo-dsp .
docker tag salesagent:yahoo-dsp 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# 2. Deploy
cd terraform/environments/staging
terraform apply

# 3. Verify
aws ecs describe-services --cluster salesagent-yahoo --services salesagent-yahoo --region us-east-1

# 4. Test (from Newton VPC)
curl http://yahoo.salesagent.local:9580/mcp/tools/get_products/call -H "Content-Type: application/json" -d '{"arguments": {}}'
```

---

## 📍 Service Discovery DNS

```
ESPN:      espn.salesagent.local:9580
CNN:       cnn.salesagent.local:9580
NYT:       nyt.salesagent.local:9580
Yahoo DSP: yahoo.salesagent.local:9580  ← NEW!
```

**Note:** DNS only resolves within VPC (Newton must be in same VPC)

---

## 🔧 Newton Configuration

```json
{
  "mcpServers": {
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp"
    }
  }
}
```

Add to Newton's MCP config and restart.

---

## 📊 Performance Metrics Comparison

### ESPN (Basic)
```json
{
  "impressions": 10000000,
  "spend": 50000,
  "avg_cpm": 5.00
}
```

### Yahoo DSP (Rich)
```json
{
  "impressions": 7692307,
  "clicks": 8461,
  "spend": 50000,
  "avg_cpm": 6.50,
  
  "bid_requests": 32000000,
  "win_rate": 0.24,
  "viewability_rate": 0.72,
  "ctr": 0.0011,
  "conversions": 190,
  "conversion_rate": 0.0225
}
```

---

## 💰 Cost

**Monthly AWS:**
- ESPN/CNN/NYT: $90/month (3 × $30)
- Yahoo DSP: +$30/month
- **Total: $120/month** for all 4 agents

---

## 🎯 When to Use Each

### Use Direct (ESPN/CNN/NYT) When:
- ✅ Need guaranteed delivery
- ✅ Know specific placements work
- ✅ Want simple, predictable pricing
- ✅ Need immediate launch

### Use DSP (Yahoo) When:
- ✅ Audience targeting is priority
- ✅ Want performance optimization
- ✅ Need broader reach (100+ sites)
- ✅ Have time for learning phase
- ✅ Want detailed analytics

---

## 🐛 Quick Troubleshooting

| Issue | Fix |
|-------|-----|
| "Unknown adapter type: yahoo_dsp" | Check `src/adapters/__init__.py` registration |
| Products showing $5.00 CPM | Re-run `init_demo_tenants_aws.py` |
| DNS doesn't resolve | Ensure Newton in same VPC |
| No bid landscape data | Check `get_media_buy_delivery()` response |

---

## 📚 Documentation

- **Full Guide:** `docs/demo/YAHOO_DSP_DEMO_GUIDE.md`
- **Implementation:** `YAHOO_DSP_IMPLEMENTATION_SUMMARY.md`
- **Deploy Steps:** `DEPLOY_YAHOO_DSP.md`
- **Source Code:** `src/adapters/yahoo_dsp.py`

---

## ✅ Success Checklist

- [ ] Yahoo DSP ECS service running
- [ ] `yahoo.salesagent.local` resolves
- [ ] `get_products` returns 3 DSP products
- [ ] Pricing shows `is_fixed: false`
- [ ] Newton has 4 MCP servers registered
- [ ] Can create campaigns on Yahoo DSP
- [ ] Performance includes DSP metrics

---

## 🎉 Result

**Before:** 3 publisher agents (direct buys only)
**After:** 3 publishers + 1 DSP (direct + programmatic)

Newton can now:
- ✅ Compare buying strategies
- ✅ Choose optimal channel per goal
- ✅ Split budgets across channels
- ✅ Optimize based on performance

**Demo-ready advertising ecosystem!** 🚀

