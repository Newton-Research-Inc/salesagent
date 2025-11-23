# Fix ECS Task Definition to Use ECR Image

## Problem

The ECS task was trying to:
1. Pull `public.ecr.aws/docker/library/python:3.11-slim`
2. Clone GitHub repo
3. Run non-existent script `./scripts/startup/docker_start_all_services.sh`

**Error**: `sh: 1: ./scripts/startup/docker_start_all_services.sh: not found`

## Solution

Updated Terraform to use our pre-built Docker image from ECR instead.

## Changes Made

1. **`terraform/modules/ecs/main.tf`**:
   - Changed `image` to use ECR: `${var.ecr_repository_url}:latest`
   - Removed broken `command` override
   - Fixed port mappings: 8080, 8001, 8091 (was 9580, 9501, 9591)
   - Added `ADCP_PORT` and `ADCP_HOST` environment variables

2. **`terraform/modules/ecs/variables.tf`**:
   - Added `ecr_repository_url` variable

3. **`terraform/environments/staging/main.tf`**:
   - Passed `ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"`

## Apply Changes

```bash
cd /Users/danfinkel/github/opensource/salesagent/terraform/environments/staging

# Re-apply Terraform
terraform init
terraform apply -auto-approve

# Force new deployment with updated task definition
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-staging \
  --force-new-deployment \
  --task-definition $(aws ecs describe-services \
    --cluster salesagent-staging \
    --services salesagent-staging \
    --query 'services[0].taskDefinition' \
    --output text --region us-east-1) \
  --region us-east-1
```

## Expected Result

After apply + force-new-deployment:
- ✅ Container uses our ECR image with all code pre-installed
- ✅ Dockerfile's `ENTRYPOINT` runs (`./scripts/deploy/entrypoint.sh`)
- ✅ Database auto-initializes on first startup
- ✅ All 3 services start: MCP (8080), Admin (8001), A2A (8091)
- ✅ Health checks pass after ~2-3 minutes

Test:
```bash
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/mcp/health
```

Expected: `{"status": "healthy", "tenant": "espn"}`

