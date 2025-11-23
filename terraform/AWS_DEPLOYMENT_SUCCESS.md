# 🎉 AWS Deployment SUCCESS!

**Date**: November 23, 2025  
**Environment**: Staging (Newton Demo)  
**Region**: us-east-1  
**VPC**: Newton's existing VPC (vpc-0c3f93c08fc1d2530)  

---

## ✅ DEPLOYED INFRASTRUCTURE

### 🌐 Application Load Balancer
- **DNS Name**: `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com`
- **Public HTTP** (port 80)
- **Host-based routing** for ESPN, CNN, NYT subdomains

### 💾 Database (RDS PostgreSQL)
- **Endpoint**: `staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432`
- **Engine**: PostgreSQL 15.15
- **Instance**: db.t4g.micro (2 vCPU, 1GB RAM)
- **Storage**: 20GB GP3 (auto-scaling to 40GB)
- **Backup**: 7-day retention
- **Multi-AZ**: Disabled (staging)
- **Credentials**:
  - Username: `salesagent`
  - Password: `SalesAgent2024Demo!`
  - Database: `salesagent`

### 🐳 ECS Fargate
- **Cluster**: salesagent-staging
- **Service**: salesagent-staging (1 task)
- **Task**: 0.5 vCPU, 1GB RAM
- **Ports**: 9580 (MCP), 9501 (Admin), 9591 (A2A)
- **Logs**: CloudWatch `/ecs/salesagent-staging`

### 🔐 Secrets Manager
- `staging-salesagent-gemini-api-key`: Placeholder
- `staging-salesagent-google-client-id`: Placeholder
- `staging-salesagent-google-client-secret`: Placeholder

### 🛡️ Security Groups
- **ALB SG**: Allows HTTP/HTTPS from internet
- **ECS SG**: Allows traffic from ALB only
- **RDS SG**: Allows PostgreSQL from ECS only

---

## 📋 NEXT STEPS

### 1. DNS Configuration (REQUIRED)

Create **9 CNAME records** in your DNS provider:

```
# MCP Endpoints
mcp-espn.adcp-salesagent.com  → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
mcp-cnn.adcp-salesagent.com   → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
mcp-nyt.adcp-salesagent.com   → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com

# Admin UI Endpoints
admin-espn.adcp-salesagent.com → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
admin-cnn.adcp-salesagent.com  → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
admin-nyt.adcp-salesagent.com  → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com

# A2A Endpoints
a2a-espn.adcp-salesagent.com   → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
a2a-cnn.adcp-salesagent.com    → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
a2a-nyt.adcp-salesagent.com    → salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
```

**Testing DNS**:
```bash
# Wait 5-10 minutes for DNS propagation, then test:
dig mcp-espn.adcp-salesagent.com +short
# Should return: salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
```

### 2. Database Initialization (REQUIRED)

The ECS task is currently trying to start but will fail because:
1. The database is empty (no schema)
2. No demo data (tenants, principals, products)

**Option A: Connect via bastion** (recommended for production):
```bash
# SSH tunnel through a bastion host
# (You'll need to set up a bastion host in Newton's VPC)
```

**Option B: Temporarily allow your IP** (quick for demo):
```bash
# Get your current IP
MY_IP=$(curl -s ifconfig.me)

# Add inbound rule to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr ${MY_IP}/32 \
  --region us-east-1

# Connect to database
psql "postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# Run migrations
# (Need to copy migration files and run alembic)

# IMPORTANT: Remove the rule after setup
aws ec2 revoke-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr ${MY_IP}/32 \
  --region us-east-1
```

**Better Option C: Use ECS Exec** (AWS SSM):
```bash
# Enable ECS Exec (requires updating task definition)
# Then connect to running container
aws ecs execute-command \
  --cluster salesagent-staging \
  --task <task-id> \
  --container salesagent \
  --interactive \
  --command "/bin/bash"

# Inside container, run migrations
cd /app
uv run python migrate.py
uv run python scripts/setup/init_database_ci.py
```

### 3. Fix ECS Task Definition

Current task definition has issues:
1. **Docker image**: Uses base `python:3.11-slim` and clones from git
2. **Startup script**: Expects `./scripts/startup/docker_start_all_services.sh`
3. **Port mismatch**: Container uses 9580/9501/9591 but expects different ports

**Recommended Fix**: Build and push proper Docker image

```bash
# Build Docker image
cd /Users/danfinkel/github/opensource/salesagent
docker build -t salesagent:staging -f Dockerfile .

# Create ECR repository
aws ecr create-repository --repository-name salesagent-staging --region us-east-1

# Tag and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 381492092437.dkr.ecr.us-east-1.amazonaws.com
docker tag salesagent:staging 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

# Update ECS task definition to use ECR image
# (Requires Terraform changes in modules/ecs/main.tf)
```

### 4. Test Endpoints

Once DNS is configured and services are running:

```bash
# Test ALB directly (no DNS needed)
curl -I http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/health

# Test MCP endpoint (after DNS)
curl -I http://mcp-espn.adcp-salesagent.com/health

# Test Admin UI (after DNS)
curl -I http://admin-espn.adcp-salesagent.com/health
```

### 5. Newton Integration

Update Newton's MCP client configuration:

```json
{
  "espn_sales_agent": {
    "url": "http://mcp-espn.adcp-salesagent.com/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  },
  "cnn_sales_agent": {
    "url": "http://mcp-cnn.adcp-salesagent.com/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  },
  "nyt_sales_agent": {
    "url": "http://mcp-nyt.adcp-salesagent.com/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  }
}
```

### 6. Optional: SSL/TLS (HTTPS)

For production use, add HTTPS:

```bash
# Request ACM certificate
aws acm request-certificate \
  --domain-name "*.adcp-salesagent.com" \
  --validation-method DNS \
  --region us-east-1

# Add HTTPS listener to ALB (requires Terraform changes)
# Update ALB listener rules to redirect HTTP → HTTPS
```

---

## 🐛 CURRENT ISSUES

### Issue 1: ECS Task Failing to Start

**Problem**: ECS task is starting but likely failing because:
- Database has no schema
- Startup script path is incorrect
- Git clone approach is slow and unreliable

**Check task status**:
```bash
aws ecs describe-tasks \
  --cluster salesagent-staging \
  --tasks $(aws ecs list-tasks --cluster salesagent-staging --service-name salesagent-staging --query 'taskArns[0]' --output text) \
  --region us-east-1
```

**Check logs**:
```bash
aws logs tail /ecs/salesagent-staging --follow --region us-east-1
```

### Issue 2: No Demo Data

Database needs:
- Alembic migrations (schema creation)
- 3 tenants (ESPN, CNN, NYT)
- Principals (Nike, Coca-Cola, Apple)
- Products for each tenant
- AuthorizedProperty records
- PricingOption records

**Solution**: Create database initialization script for AWS deployment

---

## 💰 COST BREAKDOWN

### Monthly Costs (~$45-50/month)

| Service | Size | Cost |
|---------|------|------|
| **RDS PostgreSQL** | db.t4g.micro, 20GB | ~$15 |
| **ECS Fargate** | 0.5 vCPU, 1GB RAM | ~$15 |
| **Application Load Balancer** | - | ~$18 |
| **Data Transfer** | Minimal | ~$2-5 |
| **CloudWatch Logs** | 7-day retention | ~$1 |
| **Secrets Manager** | 3 secrets | ~$1.20 |
| **TOTAL** | | **~$52/month** |

### Cost Savings (~$40/month)

By reusing Newton's VPC infrastructure:
- **NAT Gateway**: $32/month saved (already exists in Newton's VPC)
- **VPC costs**: $8/month saved
- **Network efficiency**: Lower data transfer costs

**Without VPC reuse, total would be ~$92/month**

---

## 📊 MONITORING

### CloudWatch Dashboards

**ECS Service Health**:
```bash
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-staging \
  --region us-east-1 \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount,Failed:failures}'
```

**ALB Health Checks**:
```bash
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-east-1:381492092437:targetgroup/salesagent-staging-mcp/56eba73972b52788 \
  --region us-east-1
```

**RDS Metrics**:
- CPU Utilization
- Database Connections
- Free Storage Space
- Read/Write IOPS

### Alarms to Create

```bash
# High CPU on RDS
aws cloudwatch put-metric-alarm \
  --alarm-name salesagent-rds-high-cpu \
  --alarm-description "RDS CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region us-east-1

# ECS Task Failures
aws cloudwatch put-metric-alarm \
  --alarm-name salesagent-ecs-task-failures \
  --alarm-description "ECS task count < 1" \
  --metric-name DesiredTaskCount \
  --namespace AWS/ECS \
  --statistic Average \
  --period 60 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 2 \
  --region us-east-1
```

---

## 🔧 TROUBLESHOOTING

### "Service Unavailable" on ALB

**Causes**:
1. No healthy targets in target groups
2. ECS tasks not starting
3. Health check failing

**Debug**:
```bash
# Check target health
aws elbv2 describe-target-health --target-group-arn <TARGET-GROUP-ARN>

# Check ECS tasks
aws ecs list-tasks --cluster salesagent-staging

# Check task logs
aws logs tail /ecs/salesagent-staging --follow
```

### Database Connection Errors

**Causes**:
1. Security group blocking connections
2. Wrong credentials
3. Database not available

**Debug**:
```bash
# Test connection from local (if security group allows)
psql "postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier staging-salesagent-db \
  --query 'DBInstances[0].DBInstanceStatus'
```

### DNS Not Resolving

**Causes**:
1. DNS not configured yet
2. DNS propagation delay (5-10 minutes)
3. Wrong CNAME target

**Debug**:
```bash
# Check DNS resolution
dig mcp-espn.adcp-salesagent.com +short

# Check if pointing to correct ALB
nslookup mcp-espn.adcp-salesagent.com
```

---

## 📝 TERRAFORM STATE

**State Location**: Local (in `/terraform/environments/staging/terraform.tfstate`)

**⚠️ IMPORTANT**: 
- State is NOT in S3 (we disabled S3 backend due to SSO credential issues)
- DO NOT lose this file or you'll lose ability to manage infrastructure
- Consider uploading to S3 manually once SSO issues are resolved

**To migrate to S3 backend later**:
```bash
# 1. Update main.tf to uncomment S3 backend
# 2. Run: terraform init -migrate-state
```

---

## 🚀 FUTURE IMPROVEMENTS

### 1. GitHub Actions CI/CD

Create `.github/workflows/deploy-aws.yml`:
```yaml
name: Deploy to AWS

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
      - name: Push to ECR
      - name: Update ECS service
```

### 2. Auto-scaling

Add auto-scaling to ECS service based on:
- CPU utilization > 70%
- Memory utilization > 80%
- Request count per target

### 3. SSL/TLS

- Request ACM certificate for `*.adcp-salesagent.com`
- Add HTTPS listener to ALB
- Redirect HTTP → HTTPS

### 4. Database Backups

- Already configured: 7-day automated backups
- Consider: Cross-region backup replication
- Consider: Manual snapshots before major changes

### 5. Monitoring & Alerting

- CloudWatch dashboards for all services
- SNS topics for critical alerts
- PagerDuty/Slack integration

---

## 📞 SUPPORT

**Terraform Issues**:
- Check `terraform/AWS_SETUP_GUIDE.md`
- Run: `terraform plan` to see what would change
- Run: `terraform state list` to see what's managed

**AWS Console**:
- ECS: https://console.aws.amazon.com/ecs/v2/clusters/salesagent-staging
- RDS: https://console.aws.amazon.com/rds/home?region=us-east-1#database:id=staging-salesagent-db
- ALB: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LoadBalancers:

**Logs**:
```bash
# ECS logs
aws logs tail /ecs/salesagent-staging --follow

# RDS logs
aws rds download-db-log-file-portion \
  --db-instance-identifier staging-salesagent-db \
  --log-file-name error/postgresql.log
```

---

**Deployment Date**: November 23, 2025  
**Deployed By**: Terraform via AWS SSO  
**Environment**: Staging (Newton Demo)  
**Region**: us-east-1  
**Account**: 381492092437

