# Deploy Yahoo DSP - Quick Start Guide

## ✅ What's Done

All code is complete and pushed to GitHub (`staging` branch, commit `b43a280c`):

- ✅ Yahoo DSP adapter (`src/adapters/yahoo_dsp.py`)
- ✅ Demo products with programmatic characteristics
- ✅ Tenant initialization script updated
- ✅ Terraform ECS configuration for Yahoo
- ✅ Service Discovery integration
- ✅ Comprehensive documentation

---

## 🚀 Deployment Steps (Run These Next)

### Step 1: Build and Push Docker Image

**⚠️ IMPORTANT:** Build for AMD64 architecture (ECS runs on x86_64, not ARM).

```bash
# From your local machine
cd /Users/danfinkel/github/opensource/salesagent

# Pull latest changes (already on staging branch)
git pull origin staging

# Build Docker image for AMD64 (ECS architecture)
# This is critical if building on Apple Silicon (M1/M2/M3)
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

**Expected Time:** 5-10 minutes

**Note:** The `--platform linux/amd64` flag ensures the image runs on ECS (x86_64). Without it, you'll see `exec format error` on Apple Silicon Macs.

---

### Step 2: Deploy to AWS with Terraform

```bash
cd terraform/environments/staging

# Review changes (Yahoo DSP addition)
terraform plan

# Expected changes:
# + module.ecs_yahoo (new ECS service)
# + Yahoo Service Discovery registration
# ~ Updated outputs (yahoo URLs)

# Deploy
terraform apply

# Type 'yes' when prompted
```

**Expected Output:**
```
Apply complete! Resources: 3 added, 1 changed, 0 destroyed.

Outputs:
service_discovery_dns = {
  espn  = "espn.salesagent.local:9580"
  cnn   = "cnn.salesagent.local:9580"
  nyt   = "nyt.salesagent.local:9580"
  yahoo = "yahoo.salesagent.local:9580"  # ← New!
}
```

**Expected Time:** 5-8 minutes

---

### Step 3: Verify Yahoo DSP is Running

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster salesagent-yahoo \
  --services salesagent-yahoo \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,DesiredCount:desiredCount}'

# Expected:
# {
#   "Status": "ACTIVE",
#   "Running": 1,
#   "DesiredCount": 1
# }

# Check Service Discovery DNS registration
aws servicediscovery list-services --region us-east-1 | grep yahoo

# Expected: Should see yahoo service registered

# View logs (optional)
aws logs tail /ecs/salesagent-yahoo --follow --region us-east-1
```

**Expected Time:** 2 minutes

---

### Step 4: Verify Yahoo Tenant Initialized

The tenant should initialize automatically via `entrypoint.sh` when the ECS task starts (triggered by `ADCP_TESTING=true`).

To verify:

```bash
# Option A: Check logs for initialization
aws logs filter-log-events \
  --log-group-name /ecs/salesagent-yahoo \
  --filter-pattern "Creating tenant: yahoo" \
  --region us-east-1

# Expected: Should see "✅ Created tenant yahoo with products and principal"

# Option B: Connect to database and check
# (or wait for Newton test in Step 5 - if products return, tenant exists)
```

**Expected Time:** 1 minute

---

### Step 5: Test from Newton (Inside VPC)

**From Newton instance** (must be in same VPC):

```bash
# Test DNS resolution
dig yahoo.salesagent.local

# Expected: Should resolve to private IP (10.0.x.x)

# Test MCP endpoint
curl http://yahoo.salesagent.local:9580/mcp/

# Expected: MCP server info (FastMCP response)

# Test get_products
curl http://yahoo.salesagent.local:9580/mcp/tools/get_products/call \
  -H "Content-Type: application/json" \
  -d '{"arguments": {}}'

# Expected: 3 Yahoo DSP products (Audience-Targeted Display, Premium Display + Retargeting, Mobile Audience Network)
```

**Expected Time:** 2 minutes

---

### Step 6: Update Newton MCP Configuration

Add Yahoo DSP to Newton's MCP server list:

```json
{
  "mcpServers": {
    "espn_sales_agent": {
      "url": "http://espn.salesagent.local:9580/mcp"
    },
    "cnn_sales_agent": {
      "url": "http://cnn.salesagent.local:9580/mcp"
    },
    "nyt_sales_agent": {
      "url": "http://nyt.salesagent.local:9580/mcp"
    },
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp"
    }
  }
}
```

**Configuration File Location:** Check Newton's MCP config location (varies by setup)

**Expected Time:** 2 minutes

---

### Step 7: Restart Newton Services

```bash
# Restart Newton to load new MCP server
# (Command depends on how Newton is deployed - systemd, Docker, etc.)

# Example (systemd):
sudo systemctl restart newton

# Example (Docker):
docker restart newton

# Example (Kubernetes):
kubectl rollout restart deployment/newton
```

**Expected Time:** 1 minute

---

### Step 8: Test End-to-End Campaign Creation

**From Newton** (via UI or API):

```bash
# 1. Get products from Yahoo DSP
newton_cli mcp call yahoo_dsp get_products

# Expected: Returns 3 DSP products with audience-targeting descriptions

# 2. Create test campaign
newton_cli mcp call yahoo_dsp create_media_buy \
  --buyer_ref "test_dsp_nike" \
  --brand_manifest '{"name": "Nike", "url": "https://nike.com"}' \
  --packages '[{
    "package_id": "test_yahoo_728x90",
    "product_id": "yahoo_display_728x90",
    "budget": 10000,
    "creative_ids": ["nike_test_creative"]
  }]'

# Expected Response:
# {
#   "status": "pending_review",  # DSP campaigns require approval
#   "media_buy_id": "yahoo_dsp_<campaign_id>",
#   "bid_landscape": {
#     "median_winning_bid": 6.83,
#     "competition_level": "medium",
#     ...
#   },
#   "estimated_reach": { "estimated_unique_users": 2500000, ... }
# }

# 3. Get campaign performance (simulated)
newton_cli mcp call yahoo_dsp get_media_buy_delivery \
  --media_buy_id "yahoo_dsp_<campaign_id>"

# Expected: Rich DSP metrics (win_rate, viewability, conversions)
```

**Expected Time:** 3-5 minutes

---

## ✅ Success Checklist

After completing all steps, verify:

- [ ] Yahoo DSP ECS service is ACTIVE with 1 running task
- [ ] Service Discovery DNS `yahoo.salesagent.local` resolves
- [ ] `curl http://yahoo.salesagent.local:9580/mcp/` returns MCP server info
- [ ] `get_products` returns 3 Yahoo DSP products
- [ ] Product names mention "Audience-Targeted" or "Retargeting"
- [ ] Pricing shows `is_fixed: false` (bid-based)
- [ ] Newton has 4 MCP servers registered (ESPN, CNN, NYT, Yahoo DSP)
- [ ] Newton can create campaigns on Yahoo DSP
- [ ] Campaign response includes `bid_landscape` data
- [ ] Performance metrics include `win_rate`, `viewability_rate`, `conversions`

---

## 🎯 Demo Ready!

Once all checks pass, you can demo:

### Compare Direct vs Programmatic

```
Newton: "Buy $50K Nike Air Jordan campaign"

ESPN (Direct):
- $5.00 CPM fixed
- 10M impressions guaranteed
- ESPN homepage placement
→ Simple, predictable, immediate

Yahoo DSP (Programmatic):
- $6.50 CPM bid-based
- ~7.7M impressions estimated
- Audience targeting (auto_intenders)
→ Targeted, optimized, higher CPM justified
```

### Show Performance Differences

```
ESPN Metrics:
- Impressions: 10M
- Spend: $50K
- Avg CPM: $5.00

Yahoo DSP Metrics (+ all ESPN metrics):
- Bid requests: 32M
- Win rate: 31%
- Viewability: 72%
- CTR: 0.11%
- Conversions: 195
- Conversion rate: 2.4%
```

---

## 📊 Cost Impact

**New Monthly Costs:**
- Yahoo DSP Fargate task: +$30/month
- **Total: $135/month** (was $105/month)

**Per Agent:** $30/month for full ECS + Service Discovery

---

## 📚 Documentation References

- **Yahoo DSP Demo Guide:** `docs/demo/YAHOO_DSP_DEMO_GUIDE.md` (600+ lines)
- **Implementation Summary:** `YAHOO_DSP_IMPLEMENTATION_SUMMARY.md`
- **Newton Config Example:** `docs/demo/NEWTON_MCP_CONFIG_YAHOO.json`
- **Adapter Source Code:** `src/adapters/yahoo_dsp.py` (730 lines)

---

## 🐛 Troubleshooting

### Issue: `exec /bin/bash: exec format error` in ECS logs

**Symptom:**
```bash
aws logs tail /ecs/salesagent-yahoo --follow --region us-east-1
# Shows: exec /bin/bash: exec format error
```

**Cause:** Docker image built for wrong CPU architecture (ARM64 instead of AMD64).

**Fix:** Rebuild with correct architecture:
```bash
cd /Users/danfinkel/github/opensource/salesagent

# Rebuild for AMD64 (ECS architecture)
docker build --platform linux/amd64 -t salesagent:yahoo-dsp .

# Tag and push
docker tag salesagent:yahoo-dsp \
  381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# Force ECS to pull new image and restart
aws ecs update-service \
  --cluster salesagent-yahoo \
  --service salesagent-yahoo \
  --force-new-deployment \
  --region us-east-1

# Wait 2-3 minutes, then check logs again
aws logs tail /ecs/salesagent-yahoo --follow --region us-east-1
# Should now see: 🚀 Starting AdCP Sales Agent...
```

### Issue: ECS service shows "Running: 0" despite "DesiredCount: 1"

**Cause:** Task is crashing on startup (usually architecture mismatch).

**Fix:** Check logs with `aws logs tail /ecs/salesagent-yahoo --follow` and apply fix above.

### Issue: Docker push fails with certificate error

**Fix:** Use `required_permissions: ['all']` or configure AWS SSO:
```bash
aws sso login
aws ecr get-login-password --region us-east-1 | docker login ...
```

### Issue: Terraform apply fails on Service Discovery

**Fix:** Service Discovery namespace already exists from ESPN/CNN/NYT - this is expected. Yahoo DSP reuses the same namespace.

### Issue: Yahoo tenant not initialized

**Fix:** Run manually:
```bash
# SSH to any ECS task or run locally with DATABASE_URL set
python scripts/setup/init_demo_tenants_aws.py
```

### Issue: Newton can't resolve yahoo.salesagent.local

**Fix:** Ensure Newton is in the same VPC (vpc-0c3f93c08fc1d2530). Service Discovery DNS only works within VPC.

### Issue: Products showing $5.00 CPM instead of $6.50

**Fix:** Check database - Yahoo products should have different pricing than ESPN/CNN/NYT. Re-run `init_demo_tenants_aws.py` if needed.

---

## 🎉 All Set!

After deployment, you'll have:

✅ **4 Sales Agents:**
- ESPN (publisher) - espn.salesagent.local
- CNN (publisher) - cnn.salesagent.local
- NYT (publisher) - nyt.salesagent.local
- Yahoo DSP (programmatic) - yahoo.salesagent.local

✅ **Stable DNS Names** (no more IP changes!)

✅ **Both Buying Models:**
- Direct: Guaranteed, placement-based, fixed CPM
- Programmatic: Audience-targeted, auction-based, dynamic CPM

✅ **Rich Demo Scenarios:**
- Compare direct vs programmatic
- Show audience targeting value
- Demonstrate performance optimization
- Prove AdCP protocol flexibility

**Ready for Newton demos!** 🚀

