# AWS Deployment Guide - Complete Walkthrough

## Overview

This guide covers the complete deployment process:
1. **Docker Image** - Build and push to AWS ECR
2. **Database Setup** - Initialize schema and demo data
3. **ECS Deployment** - Deploy sales agent services
4. **Verification** - Test all endpoints

---

## Part 1: Docker Image Deployment

### Prerequisites

- AWS CLI configured (`aws sso login`)
- Docker installed
- ECR repository created (done via Terraform)

### Build Docker Image

**Important:** If on Apple Silicon (M1/M2/M3), build for AMD64:

```bash
cd /Users/danfinkel/github/opensource/salesagent

# Pull latest code
git pull origin staging

# Build for AMD64 (ECS runs on x86_64)
docker build --platform linux/amd64 -t salesagent:staging .

# Or for local testing (uses your architecture)
docker build -t salesagent:staging .
```

### Push to ECR

```bash
# Get ECR repository URL from Terraform
cd terraform/environments/staging
ECR_URL=$(terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Tag image
docker tag salesagent:staging $ECR_URL:latest

# Push to ECR
docker push $ECR_URL:latest
```

### Verify Image Upload

```bash
# List images in ECR
aws ecr list-images \
  --repository-name salesagent-staging \
  --region us-east-1

# Expected output: Shows "latest" tag with digest
```

---

## Part 2: Database Initialization

### Architecture Context

The RDS database is in a **private subnet** and only accepts connections from:
1. ECS tasks (via security group rules)
2. Your local IP (for initialization only)

### Step 1: Allow Your IP Temporarily

```bash
# Get your public IP
YOUR_IP=$(curl -s ifconfig.me)
echo "Your IP: $YOUR_IP"

# Get RDS security group from Terraform
cd terraform/environments/staging
RDS_SG=$(terraform output -raw database_security_group_id)

# Add temporary ingress rule
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --cidr $YOUR_IP/32 \
  --region us-east-1
```

### Step 2: Test Database Connection

```bash
# Get database endpoint from Terraform
DB_ENDPOINT=$(terraform output -raw database_endpoint | cut -d: -f1)
DB_PASSWORD=$(terraform output -raw database_password)

# Test connection
psql "postgresql://salesagent:$DB_PASSWORD@$DB_ENDPOINT:5432/salesagent"

# If connected successfully, type \q to quit
```

### Step 3: Initialize Schema

**Option A: Let ECS Handle It (Recommended)**

The `entrypoint.sh` script automatically runs migrations and initializes demo tenants on first startup. Just deploy the ECS services (Part 3) and they'll initialize the database automatically.

**Option B: Manual Initialization**

```bash
cd /Users/danfinkel/github/opensource/salesagent

# Set database URL
export DATABASE_URL="postgresql://salesagent:$DB_PASSWORD@$DB_ENDPOINT:5432/salesagent"

# Run migrations
uv run python scripts/ops/migrate.py

# Initialize demo tenants
uv run python scripts/setup/init_demo_tenants_aws.py

# Verify
psql $DATABASE_URL -c "SELECT tenant_id, name, ad_server FROM tenants;"

# Expected: espn, cnn, nyt, yahoo rows
```

### Step 4: Remove Your IP Access

```bash
# Remove temporary ingress rule (security best practice)
aws ec2 revoke-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --cidr $YOUR_IP/32 \
  --region us-east-1
```

---

## Part 3: ECS Service Deployment

### Deploy with Terraform

```bash
cd terraform/environments/staging

# Review changes
terraform plan

# Apply (creates/updates 4 ECS services)
terraform apply

# Type 'yes' when prompted
```

### What Gets Created

| Service | Tenant | Cluster | Port | DNS |
|---------|--------|---------|------|-----|
| `salesagent-espn` | ESPN | `salesagent-espn` | 9580 | `espn.salesagent.local` |
| `salesagent-cnn` | CNN | `salesagent-cnn` | 9580 | `cnn.salesagent.local` |
| `salesagent-nyt` | NYT | `salesagent-nyt` | 9580 | `nyt.salesagent.local` |
| `salesagent-yahoo` | Yahoo DSP | `salesagent-yahoo` | 9580 | `yahoo.salesagent.local` |

### Verify Services are Running

```bash
# Check all services
for tenant in espn cnn nyt yahoo; do
  echo "=== $tenant ==="
  aws ecs describe-services \
    --cluster salesagent-$tenant \
    --services salesagent-$tenant \
    --region us-east-1 \
    --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
done

# Expected output for each:
# {
#   "Status": "ACTIVE",
#   "Running": 1,
#   "Desired": 1
# }
```

### Get Service Discovery DNS Names

```bash
cd terraform/environments/staging
terraform output service_discovery_dns

# Expected output:
# {
#   "espn" = "espn.salesagent.local:9580"
#   "cnn" = "cnn.salesagent.local:9580"
#   "nyt" = "nyt.salesagent.local:9580"
#   "yahoo" = "yahoo.salesagent.local:9580"
# }
```

### Force New Deployment (if needed)

If you pushed a new Docker image and want to force tasks to pull it:

```bash
for tenant in espn cnn nyt yahoo; do
  aws ecs update-service \
    --cluster salesagent-$tenant \
    --service salesagent-$tenant \
    --force-new-deployment \
    --region us-east-1
done
```

---

## Part 4: Verification

### From Newton (or any EC2 in VPC)

```bash
# Test DNS resolution
dig espn.salesagent.local +short
dig cnn.salesagent.local +short
dig nyt.salesagent.local +short
dig yahoo.salesagent.local +short

# Test health endpoints
curl http://espn.salesagent.local:9580/health
curl http://cnn.salesagent.local:9580/health
curl http://nyt.salesagent.local:9580/health
curl http://yahoo.salesagent.local:9580/health

# Test MCP tools
curl -X POST http://espn.salesagent.local:9580/mcp/tools/get_products/call \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"brief": "sports inventory"}}'
```

### Check ECS Logs

```bash
# View logs for ESPN service
aws logs tail /ecs/salesagent-espn \
  --follow \
  --region us-east-1

# Look for:
# ✅ "Database connection successful"
# ✅ "Demo tenants initialized"
# ✅ "Starting all services with unified routing"
```

### Common Issues

**Issue: Task keeps restarting (CrashLoopBackOff)**

Check logs:
```bash
aws logs tail /ecs/salesagent-espn --region us-east-1 | tail -50
```

Common causes:
- Database connection failed (check security groups)
- Missing environment variables (check task definition)
- Docker image platform mismatch (rebuild with `--platform linux/amd64`)

**Issue: "exec /bin/bash: exec format error"**

**Cause:** Docker image built for wrong architecture (ARM64 on Apple Silicon)

**Fix:**
```bash
# Rebuild for AMD64
docker build --platform linux/amd64 -t salesagent:staging .

# Tag and push
docker tag salesagent:staging $ECR_URL:latest
docker push $ECR_URL:latest

# Force new deployment
aws ecs update-service --cluster salesagent-espn --service salesagent-espn --force-new-deployment --region us-east-1
```

**Issue: DNS doesn't resolve (espn.salesagent.local)**

**Cause:** Service Discovery DNS is VPC-only

**Fix:**
- Ensure you're querying from within the VPC (Newton EC2 instance)
- If testing locally, use ALB public endpoint instead

**Issue: "Running: 0" in ECS service**

Check task stopped reason:
```bash
aws ecs describe-tasks \
  --cluster salesagent-espn \
  --tasks $(aws ecs list-tasks --cluster salesagent-espn --service salesagent-espn --region us-east-1 --query 'taskArns[0]' --output text) \
  --region us-east-1 \
  --query 'tasks[0].stoppedReason'
```

---

## Part 5: Update Newton Configuration

### MCP Config

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

Restart Newton to load new configuration.

---

## Deployment Checklist

### Pre-Deployment
- [ ] AWS CLI configured (`aws sts get-caller-identity` works)
- [ ] Terraform initialized (`terraform init`)
- [ ] Docker image built for AMD64 (`--platform linux/amd64`)
- [ ] Latest code pulled from GitHub

### Docker Deployment
- [ ] Image pushed to ECR
- [ ] Image digest matches locally built image
- [ ] ECR scan shows no critical vulnerabilities

### Database Setup
- [ ] Temporary security group rule added
- [ ] Database connection successful
- [ ] Schema initialized (migrations ran)
- [ ] Demo tenants created (ESPN, CNN, NYT, Yahoo)
- [ ] Temporary security group rule removed

### ECS Deployment
- [ ] Terraform apply successful
- [ ] All 4 services show `Running: 1`
- [ ] Service Discovery DNS resolves
- [ ] Health endpoints return 200 OK
- [ ] MCP `/mcp/` endpoint returns server info

### Newton Integration
- [ ] Newton MCP config updated with 4 servers
- [ ] Newton restarted
- [ ] `get_products` works for all 4 agents
- [ ] Test campaign created successfully

---

## Quick Reference Commands

```bash
# Build & push Docker image
docker build --platform linux/amd64 -t salesagent:staging .
docker tag salesagent:staging $(terraform output -raw ecr_repository_url):latest
docker push $(terraform output -raw ecr_repository_url):latest

# Deploy ECS services
cd terraform/environments/staging
terraform apply

# Force redeploy (pull new image)
aws ecs update-service --cluster salesagent-espn --service salesagent-espn --force-new-deployment --region us-east-1

# Check service status
aws ecs describe-services --cluster salesagent-espn --services salesagent-espn --region us-east-1 --query 'services[0].{Status:status,Running:runningCount}'

# View logs
aws logs tail /ecs/salesagent-espn --follow --region us-east-1

# Test MCP endpoint
curl http://espn.salesagent.local:9580/mcp/
```

---

## Success!

Once all checks pass, you have:
- ✅ 4 sales agents running in AWS ECS
- ✅ Stable DNS names (Service Discovery)
- ✅ Auto-scaling and health monitoring
- ✅ Newton connected via MCP
- ✅ Ready for demos! 🚀

See `DNS_AND_SERVICE_DISCOVERY.md` for DNS configuration details.

