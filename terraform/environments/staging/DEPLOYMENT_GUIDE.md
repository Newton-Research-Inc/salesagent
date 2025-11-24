# Multi-Tenant Sales Agent Deployment Guide

## Overview

This deployment creates **3 separate sales agent ECS services** (ESPN, CNN, NYT) that Newton can connect to directly via VPC-internal networking.

## Architecture

```
Newton (10.118.x.x) 
  ├─> ESPN Sales Agent (task IP:9580/mcp) - tenant_id=espn, principal_id=nike
  ├─> CNN Sales Agent (task IP:9580/mcp) - tenant_id=cnn, principal_id=cocacola
  └─> NYT Sales Agent (task IP:9580/mcp) - tenant_id=nyt, principal_id=apple
```

**Key Benefits:**
- ✅ **Standard MCP protocol** - no custom middleware
- ✅ **Direct connection** - lower latency, more secure
- ✅ **Simple** - no ALB path routing complexity
- ✅ **Reliable** - no FastMCP middleware issues

## Prerequisites

1. ✅ AWS CLI configured with AdministratorAccess profile
2. ✅ Docker image built and pushed to ECR
3. ✅ Database initialized with demo data (ESPN, CNN, NYT tenants)

## Deployment Steps

### 1. Apply Terraform Configuration

```bash
cd terraform/environments/staging

# Initialize Terraform
terraform init

# Review the plan
terraform plan -var-file=terraform.tfvars

# Apply (creates 3 ECS services)
terraform apply -var-file=terraform.tfvars
```

**What this creates:**
- `salesagent-espn` ECS service (1 task)
- `salesagent-cnn` ECS service (1 task)
- `salesagent-nyt` ECS service (1 task)

### 2. Get Task IPs

```bash
# Run the helper script
./get_task_ips.sh

# OR manually for each service:
aws ecs list-tasks --cluster salesagent-staging --service salesagent-espn --region us-east-1 \
  | jq -r '.taskArns[0]' \
  | xargs -I {} aws ecs describe-tasks --cluster salesagent-staging --tasks {} --region us-east-1 \
  | jq -r '.tasks[0].containers[0].networkInterfaces[0].privateIpv4Address'
```

### 3. Configure Newton

Add the MCP servers to Newton's data connectors:

```json
{
  "espn_sales": {
    "type": "mcp",
    "url": "http://<espn-task-ip>:9580/mcp",
    "transport": "http",
    "description": "ESPN Sports Advertising"
  },
  "cnn_sales": {
    "type": "mcp",
    "url": "http://<cnn-task-ip>:9580/mcp",
    "transport": "http",
    "description": "CNN News Advertising"
  },
  "nyt_sales": {
    "type": "mcp",
    "url": "http://<nyt-task-ip>:9580/mcp",
    "transport": "http",
    "description": "NYT Premium News Advertising"
  }
}
```

### 4. Test Connections

From Newton's server (or any machine on the VPC):

```bash
# Test ESPN
curl http://<espn-task-ip>:9580/health

# Test CNN
curl http://<cnn-task-ip>:9580/health

# Test NYT
curl http://<nyt-task-ip>:9580/health
```

All should return `{"status": "healthy"}`.

## Troubleshooting

### Task Not Starting

```bash
# Check logs
aws logs tail /ecs/salesagent-espn --since 5m --region us-east-1

# Check service status
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-espn \
  --region us-east-1 \
  --query 'services[0].{running:runningCount,desired:desiredCount,events:events[0:3]}'
```

### Connection Refused

1. Check security group allows inbound from Newton's IP
2. Verify task is running: `aws ecs list-tasks --cluster salesagent-staging --service salesagent-espn`
3. Check task IP is correct

### Database Connection Issues

1. Verify DATABASE_URL environment variable is correct
2. Check RDS security group allows connections from ECS tasks
3. Ensure database is initialized with tenant data

## Maintenance

### Update Docker Image

```bash
# Build new image
cd /path/to/salesagent
docker build --platform linux/amd64 -t salesagent-staging:latest .

# Push to ECR
docker tag salesagent-staging:latest 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# Force new deployment for each service
aws ecs update-service --cluster salesagent-staging --service salesagent-espn --force-new-deployment --region us-east-1
aws ecs update-service --cluster salesagent-staging --service salesagent-cnn --force-new-deployment --region us-east-1
aws ecs update-service --cluster salesagent-staging --service salesagent-nyt --force-new-deployment --region us-east-1
```

### Scale Services

```bash
# Scale to 2 tasks (for high availability)
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-espn \
  --desired-count 2 \
  --region us-east-1
```

## Cost

- **3 Fargate tasks** (512 CPU, 1024 MB RAM): ~$90/month
- **RDS db.t4g.micro**: ~$15/month
- **Data transfer** (VPC-internal): Free
- **Total**: ~$105/month

## Next Steps

1. ✅ Deploy services: `terraform apply`
2. ✅ Get task IPs: `./get_task_ips.sh`
3. ✅ Configure Newton with IPs
4. 🔄 Test Newton's media buying workflow
5. 🔄 Populate demo campaigns for each publisher


