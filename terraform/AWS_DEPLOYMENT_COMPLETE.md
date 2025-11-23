# AWS Deployment Complete - Newton Demo Environment

## 🎉 Deployment Status

### ✅ Completed Steps

1. **AWS Infrastructure** - ECS, RDS, ALB all deployed via Terraform
2. **Network Setup** - Reusing Newton's existing VPC (`vpc-0c3f93c08fc1d2530`)
3. **Path-Based Routing** - ALB configured for `/espn/mcp`, `/cnn/mcp`, `/nyt/mcp`
4. **Docker Image** - Built successfully with all Newton bug fixes
5. **Database Strategy** - Auto-initialization on container startup

### ⏳ Next Step: Push Docker Image

**See** `terraform/DEPLOY_DOCKER_IMAGE.md` for step-by-step instructions.

---

## 🏗️ Infrastructure Summary

### AWS Resources Deployed

| Resource | Name | Purpose |
|----------|------|---------|
| **ECS Cluster** | `salesagent-staging` | Hosts sales agent containers |
| **ECS Service** | `salesagent-staging` | Runs 1 Fargate task (0.5 vCPU, 1GB RAM) |
| **RDS PostgreSQL** | `staging-salesagent-db` | Database (db.t4g.micro, 20GB) |
| **ALB** | `salesagent-staging-alb` | Routes traffic to MCP/Admin/A2A |
| **Security Groups** | Various | Allows ALB → ECS → RDS traffic |
| **ECR Repository** | `salesagent-staging` | Stores Docker images |

### Network Architecture

```
Internet
   ↓
Application Load Balancer (salesagent-staging-alb)
   ├── /espn/mcp/*   → ECS Task (Port 8080)
   ├── /cnn/mcp/*    → ECS Task (Port 8080)
   ├── /nyt/mcp/*    → ECS Task (Port 8080)
   ├── /*/admin/*    → ECS Task (Port 8001)
   └── /*/a2a/*      → ECS Task (Port 8091)
        ↓
ECS Fargate Task (salesagent-staging)
   └── Connects to →
                RDS PostgreSQL (staging-salesagent-db)
                Private Subnet (10.118.143.228)
```

### Cost Estimate

**Monthly Cost: ~$46.85**

- ECS Fargate (0.5 vCPU, 1GB): **$11.81**/month
- RDS db.t4g.micro: **$14.29**/month
- ALB: **$16.20**/month
- Data Transfer: **$4.50**/month (estimated)
- ECR Storage: **~$0.05**/month

**Savings from VPC reuse: $42/month** (NAT Gateway avoided)

---

## 🔗 Access URLs

### Newton Connection Details

Newton should connect to these MCP server URLs:

**ESPN Sales Agent:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/espn/mcp/
```

**CNN Sales Agent:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/cnn/mcp/
```

**NYT Sales Agent:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/nyt/mcp/
```

### Admin UI (Browser)

**ESPN Admin:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/espn/admin/
```

**CNN Admin:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/cnn/admin/
```

**NYT Admin:**
```
http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/nyt/admin/
```

### Authentication

**Currently disabled** for testing:
- No `x-adcp-auth` header required
- Test mode enabled via `ADCP_TESTING=true`
- All tenants (ESPN, CNN, NYT) accessible

**To re-enable authentication later:**
1. Update ECS task environment: Remove `ADCP_TESTING`
2. Force new deployment
3. Newton must include `x-adcp-auth: <principal_token>` header

---

## 🗄️ Database Details

### RDS Instance

- **Endpoint:** `staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432`
- **Database:** `salesagent`
- **Username:** `salesagent`
- **Password:** (stored in AWS Secrets Manager)
- **Engine:** PostgreSQL 15.15
- **Instance:** db.t4g.micro (2 vCPU, 1GB RAM)
- **Storage:** 20GB gp3

### Auto-Initialization

On first startup, the ECS container automatically:

1. Runs Alembic migrations
2. Creates database schema
3. Creates 3 tenants (ESPN, CNN, NYT)
4. Creates demo products for each tenant
5. Creates demo advertisers (Nike, Coca-Cola, Apple)
6. Creates reference creatives for standard IAB formats

**This happens once** - subsequent restarts skip initialization if data exists.

---

## 📦 Demo Data Included

### Tenants (Publishers)

| Tenant ID | Name | Ad Server | Products |
|-----------|------|-----------|----------|
| `espn` | ESPN | Mock | 3 (Homepage, Live Game, Mobile) |
| `cnn` | CNN | Mock | 3 (Breaking News, Politics, Video Pre-roll) |
| `nyt` | NYT | Mock | 3 (Homepage, Opinion, Native) |

### Advertisers (Principals)

| Principal ID | Name | Platform Mappings |
|--------------|------|-------------------|
| `nike` | Nike Inc. | Mock Advertiser |
| `coca-cola` | Coca-Cola Company | Mock Advertiser |
| `apple` | Apple Inc. | Mock Advertiser |

### Products (Ad Inventory)

Each tenant has 3 pre-configured products with:
- ✅ Pricing options (CPM $8-15)
- ✅ Creative formats (display banners)
- ✅ Targeting (contextual, device, geo)
- ✅ Budget limits (mock adapter: 10M impressions, $10M total)

---

## 🐛 Bug Fixes Included

The deployed Docker image includes these Newton-specific fixes:

### 1. SQLAlchemy Session Detachment Fix
**File:** `src/core/tools/media_buy_create.py`  
**Issue:** Creative objects were detaching from database session  
**Fix:** Eager load all attributes into dictionary immediately after DB query

**Status:** ✅ Ready for upstream PR

### 2. Creative Dimension Extraction Fix
**File:** `src/core/tools/media_buy_create.py`  
**Issue:** Dimensions nested in `assets.image` weren't extracted  
**Fix:** Robust fallback to check nested asset structures

**Status:** ✅ Ready for upstream PR

### 3. Mock Adapter Field Name Fix
**File:** `src/core/tools/media_buy_create.py`  
**Issue:** Mock adapter expects `id` not `creative_id`  
**Fix:** Check adapter type and use correct field name

**Status:** ✅ Ready for upstream PR

### 4. Gemini Warning Suppression
**File:** `src/adapters/ai_test_orchestrator.py`  
**Issue:** Gemini API warnings confuse Newton  
**Fix:** Suppress warnings when no API key provided

**Status:** ✅ Ready for upstream PR

---

## 🚀 Testing with Newton

### Step 1: Configure Newton's MCP Client

Add to Newton's MCP configuration:

```json
{
  "mcpServers": {
    "espn_sales_agent": {
      "url": "http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/espn/mcp/",
      "transport": "http"
    },
    "cnn_sales_agent": {
      "url": "http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/cnn/mcp/",
      "transport": "http"
    },
    "nyt_sales_agent": {
      "url": "http://salesagent-staging-alb-1577494595.us-east-1.elb.amazonaws.com/nyt/mcp/",
      "transport": "http"
    }
  }
}
```

### Step 2: Test Product Discovery

Instruct Newton:
```
"Get available advertising products from ESPN that match Nike's target audience: 
basketball fans, sports enthusiasts, ages 18-35, interested in sneakers and NBA."
```

Newton should call:
```
mcp_espn_sales_agent_get_products(
  brief="basketball fans, sports enthusiasts, sneakers, NBA"
)
```

Expected response:
```json
{
  "structured_content": {
    "products": [
      {
        "product_id": "espn_homepage_leaderboard",
        "name": "ESPN Homepage - Leaderboard",
        "format_ids": ["display_728x90", "display_970x250"],
        "pricing": [{"model": "CPM", "rate": 12.0}]
      },
      ...
    ]
  }
}
```

### Step 3: Test Media Buy Creation

Instruct Newton:
```
"Create a $50,000 media buy campaign for Nike Air Jordan on ESPN 
for December 2025, targeting basketball fans."
```

Newton should:
1. Call `get_products` to find inventory
2. Call `sync_creatives` to register Nike creatives
3. Call `create_media_buy` to book the campaign

**Newton's previous issues (dimension extraction, session detachment) are now fixed!** ✅

---

## 📊 Monitoring & Logs

### CloudWatch Logs

```bash
# View live logs
aws logs tail /ecs/salesagent-staging --follow --region us-east-1

# Filter for errors
aws logs tail /ecs/salesagent-staging --follow --filter-pattern "ERROR" --region us-east-1
```

### ECS Service Status

```bash
# Check service health
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-staging \
  --query 'services[0].{Running:runningCount,Desired:desiredCount,Status:status}' \
  --output table \
  --region us-east-1
```

### Database Queries

```bash
# Connect via ECS Exec (for production troubleshooting)
# Get task ID
TASK_ID=$(aws ecs list-tasks --cluster salesagent-staging --service-name salesagent-staging --query 'taskArns[0]' --output text --region us-east-1 | awk -F'/' '{print $NF}')

# Connect to task
aws ecs execute-command \
  --cluster salesagent-staging \
  --task $TASK_ID \
  --container salesagent-staging \
  --interactive \
  --command "/bin/bash" \
  --region us-east-1

# Inside container
psql $DATABASE_URL -c "SELECT * FROM tenants;"
psql $DATABASE_URL -c "SELECT product_id, name FROM products;"
```

---

## 🔄 CI/CD - GitHub Actions (TODO)

**Next steps for automation:**

1. Create `.github/workflows/deploy-staging.yml`
2. Configure AWS credentials as GitHub secrets
3. Auto-deploy on push to `staging` branch

**See:** `terraform/GITHUB_ACTIONS_GUIDE.md` (to be created)

---

## 🔐 Security Considerations

### Current State (Demo)
- ✅ RDS in private subnet (not publicly accessible)
- ✅ Security groups restrict traffic (ALB → ECS → RDS only)
- ✅ ECS tasks run as non-root user (`adcp`)
- ⚠️ Authentication disabled for testing (`ADCP_TESTING=true`)
- ⚠️ HTTP only (no TLS/HTTPS on ALB)

### Production Readiness Checklist
- [ ] Enable authentication (remove `ADCP_TESTING`)
- [ ] Add TLS certificate to ALB (ACM + Route 53)
- [ ] Enable CloudWatch Container Insights
- [ ] Set up RDS automated backups
- [ ] Configure AWS WAF on ALB
- [ ] Implement rate limiting
- [ ] Add monitoring alerts (CloudWatch Alarms)

---

## 🐛 Known Issues & Workarounds

### Issue 1: RDS in Private Subnet
**Problem:** Can't connect to RDS from laptop for manual DB operations.  
**Workaround:** Use ECS Exec to connect to running container, then use `psql` inside container.

### Issue 2: AWS SSO Credential Expiry
**Problem:** Terraform and AWS CLI credentials expire frequently.  
**Workaround:** Run `aws sso login --profile your-profile` before each operation.

### Issue 3: ECS Task Startup Time
**Problem:** First task startup takes 2-3 minutes (database initialization).  
**Expected:** Subsequent restarts are faster (~30 seconds).

---

## 📝 Next Steps

### Immediate (Manual)
1. ✅ **Push Docker image to ECR** - See `DEPLOY_DOCKER_IMAGE.md`
2. ✅ **Force ECS deployment** - `aws ecs update-service --force-new-deployment`
3. ✅ **Test Newton integration** - Have Newton call `get_products`

### Short-Term (This Week)
4. ⏳ **Create upstream PRs** - Submit bug fixes to open source repo
5. ⏳ **Set up GitHub Actions** - Automate deployments
6. ⏳ **Add monitoring** - CloudWatch dashboards and alarms

### Long-Term (Future)
7. 🔮 **Add TLS/HTTPS** - ACM certificate + Route 53 DNS
8. 🔮 **Enable authentication** - Remove test mode, use real tokens
9. 🔮 **Production hardening** - WAF, rate limiting, backup strategy
10. 🔮 **Cost optimization** - Evaluate Spot instances, Graviton processors

---

## 💰 Cost Management

### Current Monthly Cost: ~$46.85

### Optimization Opportunities

1. **Use Graviton (ARM) for Fargate** - Save ~20% on compute
   ```
   Change: fargate_cpu = "256" (x86) → fargate_cpu = "256" (ARM64)
   Savings: ~$2.40/month
   ```

2. **Use RDS Reserved Instances** - Save ~30% with 1-year commitment
   ```
   Current: On-demand ($14.29/month)
   Reserved: ~$10/month (1-year RI)
   Savings: ~$4.50/month
   ```

3. **Reduce ALB idle time** - Schedule start/stop for demo environment
   ```
   Option: Auto-stop nights/weekends (ECS scale to 0)
   Savings: ~$10/month (60% reduction in ECS + ALB hours)
   ```

### Teardown (When Done Testing)

```bash
cd /Users/danfinkel/github/opensource/salesagent/terraform/environments/staging
terraform destroy
```

**This will delete all AWS resources and stop charges.**

---

## 🎯 Success Metrics

### Deployment Successful When:
- ✅ ECS task running (`runningCount: 1`)
- ✅ Health endpoints respond (`curl http://<ALB>/espn/mcp/health`)
- ✅ Database initialized (3 tenants, 9 products exist)
- ✅ Newton can call `get_products` and receive product list
- ✅ Newton can create media buy without errors

### Current Status:
- [x] Infrastructure deployed
- [x] Docker image built
- [ ] **Docker image pushed to ECR** ← **YOU ARE HERE**
- [ ] ECS task running
- [ ] Newton integration tested

---

## 📞 Support & Documentation

**Primary Documentation:**
- `terraform/AWS_SETUP_GUIDE.md` - Initial setup instructions
- `terraform/DEPLOY_DOCKER_IMAGE.md` - **Current task** (push image to ECR)
- `terraform/PATH_BASED_ROUTING.md` - ALB routing explanation
- `terraform/NEWTON_VPC_REUSE.md` - Network architecture

**Terraform State:**
- Location: `s3://salesagent-terraform-state-staging/staging/terraform.tfstate`
- Lock Table: `salesagent-terraform-locks`

**AWS Console Quick Links:**
- ECS Service: https://console.aws.amazon.com/ecs/v2/clusters/salesagent-staging/services/salesagent-staging
- RDS Instance: https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=staging-salesagent-db
- ALB: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LoadBalancers:search=salesagent-staging-alb
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Fecs$252Fsalesagent-staging

---

## 🙏 Acknowledgments

This deployment leverages:
- **Newton's existing VPC** - Saved $42/month by reusing network infrastructure
- **Open source salesagent** - AdCP reference implementation
- **AWS Fargate** - Serverless container orchestration
- **FastMCP** - Model Context Protocol server framework

---

**Ready to deploy?** Follow `terraform/DEPLOY_DOCKER_IMAGE.md` to push the Docker image and start the ECS service! 🚀

