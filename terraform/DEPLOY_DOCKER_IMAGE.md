# Deploy Docker Image to AWS ECS

## Status
✅ **Docker image built successfully** (`salesagent-staging:latest`)  
✅ **Image tagged for ECR**  
⏳ **Push to ECR and deploy** (manual step required)

---

## Prerequisites
- AWS credentials refreshed (run `aws sts get-caller-identity` to verify)
- Docker image built (already done ✅)

---

## Step 1: Create ECR Repository (if needed)

```bash
# Refresh AWS credentials
aws sso login --profile your-profile-name

# Create ECR repository (only needed first time)
aws ecr create-repository \
  --repository-name salesagent-staging \
  --image-scanning-configuration scanOnPush=true \
  --region us-east-1
```

Expected output:
```json
{
    "repository": {
        "repositoryName": "salesagent-staging",
        "repositoryUri": "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
    }
}
```

If you get `"RepositoryAlreadyExistsException"`, that's fine - skip to Step 2.

---

## Step 2: Login to ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 381492092437.dkr.ecr.us-east-1.amazonaws.com
```

Expected output:
```
Login Succeeded
```

---

## Step 3: Push Docker Image

```bash
cd /Users/danfinkel/github/opensource/salesagent

# Push latest tag
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# Push timestamped tag (for rollback)
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:$(date +%Y%m%d-%H%M%S)
```

This will take **2-5 minutes** to upload (~500MB compressed).

---

## Step 4: Force ECS Deployment

```bash
# Force new deployment with updated image
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-staging \
  --force-new-deployment \
  --region us-east-1
```

Expected output:
```json
{
    "service": {
        "serviceName": "salesagent-staging",
        "status": "ACTIVE",
        "desiredCount": 1
    }
}
```

---

## Step 5: Monitor Deployment

```bash
# Watch task status (repeat every 30 seconds)
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-staging \
  --query 'services[0].{Running:runningCount,Desired:desiredCount,Status:status}' \
  --output table \
  --region us-east-1

# Check recent events
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-staging \
  --query 'services[0].events[:5].[createdAt,message]' \
  --output table \
  --region us-east-1
```

Wait until `Running: 1` appears.

---

## Step 6: Verify Deployment

```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names salesagent-staging-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text \
  --region us-east-1

# Test health endpoint (replace <ALB_DNS> with actual DNS)
curl http://<ALB_DNS>/espn/mcp/health
curl http://<ALB_DNS>/cnn/mcp/health
curl http://<ALB_DNS>/nyt/mcp/health
```

Expected response:
```json
{"status": "healthy", "tenant": "espn"}
```

---

## Step 7: Connect Newton to Sales Agents

Newton can now connect to the sales agents via the ALB:

**ESPN Sales Agent:**
```
URL: http://<ALB_DNS>/espn/mcp/
```

**CNN Sales Agent:**
```
URL: http://<ALB_DNS>/cnn/mcp/
```

**NYT Sales Agent:**
```
URL: http://<ALB_DNS>/nyt/mcp/
```

**No authentication required** (test mode enabled via `ADCP_TESTING=true`).

---

## What Happens on First Startup

The ECS container will automatically:

1. ✅ Check database connectivity
2. ✅ Run Alembic migrations (`alembic upgrade head`)
3. ✅ Initialize database schema (`init_db()`)
4. ✅ Create default tenants (ESPN, CNN, NYT)
5. ✅ Create demo products, creatives, principals
6. ✅ Start MCP, Admin UI, A2A servers

**This takes ~2-3 minutes on first startup.**

---

## Troubleshooting

### Task fails to start
```bash
# Get task ARN
TASK_ARN=$(aws ecs list-tasks \
  --cluster salesagent-staging \
  --service-name salesagent-staging \
  --query 'taskArns[0]' \
  --output text \
  --region us-east-1)

# Get logs from CloudWatch
aws logs tail /ecs/salesagent-staging --follow --region us-east-1
```

### Database connection issues
- Verify RDS is in `available` state
- Check security group allows ECS → RDS (port 5432)
- Verify `DATABASE_URL` in ECS task environment variables

### ALB 502/504 errors
- ECS task is still starting (wait 2-3 minutes)
- Check task logs for startup errors
- Verify health check grace period (300 seconds)

---

## Success Criteria

✅ ECS task running (`runningCount: 1`)  
✅ Health endpoints respond (`{"status": "healthy"}`)  
✅ Database initialized (check RDS query logs)  
✅ Newton can call `get_products` on all 3 sales agents

---

## Next Steps

1. **Test Newton integration** - Have Newton call `get_products` on ESPN
2. **Monitor CloudWatch logs** - Watch for any startup errors
3. **Set up GitHub Actions** - Automate future deployments
4. **Create PRs for bug fixes** - Push SQLAlchemy and creative dimension fixes upstream

---

## Rollback (if needed)

```bash
# List previous images
aws ecr describe-images \
  --repository-name salesagent-staging \
  --query 'sort_by(imageDetails,& imagePushedAt)[-5:].imageTags' \
  --output table \
  --region us-east-1

# Update task definition to use previous tag
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-staging \
  --task-definition salesagent-staging:PREVIOUS_REVISION \
  --force-new-deployment \
  --region us-east-1
```

