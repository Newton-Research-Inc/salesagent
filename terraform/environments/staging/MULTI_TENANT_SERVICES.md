# Multi-Tenant ECS Services Configuration

This configuration creates 3 separate ECS services, one for each publisher tenant:
- ESPN (espn)
- CNN (cnn)
- NYT (nyt)

Each service runs the same Docker image but with different environment variables to set the tenant context.

## Usage

From `terraform/environments/staging/`:

```bash
# Apply the multi-tenant configuration
terraform apply -var-file=terraform.tfvars

# This will create:
# - salesagent-espn (tenant_id=espn, principal_id=nike)
# - salesagent-cnn (tenant_id=cnn, principal_id=cocacola)
# - salesagent-nyt (tenant_id=nyt, principal_id=apple)
```

## Getting Task IPs for Newton

After deployment, get the task IPs:

```bash
# ESPN
aws ecs list-tasks --cluster salesagent-staging --service salesagent-espn --region us-east-1 \
  | jq -r '.taskArns[0]' \
  | xargs -I {} aws ecs describe-tasks --cluster salesagent-staging --tasks {} --region us-east-1 \
  | jq -r '.tasks[0].containers[0].networkInterfaces[0].privateIpv4Address'

# CNN
aws ecs list-tasks --cluster salesagent-staging --service salesagent-cnn --region us-east-1 \
  | jq -r '.taskArns[0]' \
  | xargs -I {} aws ecs describe-tasks --cluster salesagent-staging --tasks {} --region us-east-1 \
  | jq -r '.tasks[0].containers[0].networkInterfaces[0].privateIpv4Address'

# NYT
aws ecs list-tasks --cluster salesagent-staging --service salesagent-nyt --region us-east-1 \
  | jq -r '.taskArns[0]' \
  | xargs -I {} aws ecs describe-tasks --cluster salesagent-staging --tasks {} --region us-east-1 \
  | jq -r '.tasks[0].containers[0].networkInterfaces[0].privateIpv4Address'
```

## Newton Connection Configuration

Use the task IPs in Newton's MCP configuration:

```json
{
  "espn_sales": {
    "type": "mcp",
    "url": "http://<espn-task-ip>:9580/mcp",
    "transport": "http"
  },
  "cnn_sales": {
    "type": "mcp",
    "url": "http://<cnn-task-ip>:9580/mcp",
    "transport": "http"
  },
  "nyt_sales": {
    "type": "mcp",
    "url": "http://<nyt-task-ip>:9580/mcp",
    "transport": "http"
  }
}
```

## Architecture

Each ECS service:
- Runs in private subnets (same as Newton)
- Uses the same Docker image (ecr/salesagent-staging:latest)
- Has tenant-specific environment variables:
  - `ADCP_TEST_TENANT_ID`: Tenant identifier (espn/cnn/nyt)
  - `ADCP_TEST_PRINCIPAL_ID`: Default principal for testing (nike/cocacola/apple)
- Exposes port 9580 for MCP server
- No ALB needed (VPC-internal traffic only)

## Cost

- **Same as current**: 3 tasks running simultaneously (instead of 1)
- **No additional ALB cost**: MCP traffic is VPC-internal
- **Estimated cost**: ~$30/month for 3 Fargate tasks (512 CPU, 1024 MB RAM each)

