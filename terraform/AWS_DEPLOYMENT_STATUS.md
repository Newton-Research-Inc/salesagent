# AWS Newton Demo Deployment - Progress Report

## ✅ COMPLETED

### Infrastructure as Code Setup
1. **Terraform Module Structure Created**
   - `/terraform/modules/alb/` - Application Load Balancer with target groups for MCP, Admin, A2A
   - `/terraform/modules/database/` - RDS PostgreSQL with security groups and monitoring
   - `/terraform/modules/ecs/` - ECS Fargate cluster with task definitions and services
   
2. **Environment Configuration**
   - `/terraform/environments/staging/main.tf` - Main configuration using Newton's VPC
   - Variables defined for domain, passwords, API keys, secrets
   - Reuses Newton's existing VPC (`vpc-0c3f93c08fc1d2530`) to save ~$40/month
   
3. **Security Configuration**
   - AWS Secrets Manager for storing API keys and OAuth credentials
   - Security groups for ALB, ECS tasks, and RDS
   - IAM roles for ECS task execution and RDS monitoring
   
4. **Network Architecture**
   - Leverages Newton's existing:
     - VPC (`vpc-0c3f93c08fc1d2530`)
     - Public subnets (`dev-subnet-public*`)
     - Private subnets (`dev-subnet-private*`)
     - Internet Gateway
     - NAT Gateways
   - New resources:
     - Application Load Balancer in public subnets
     - RDS PostgreSQL in private subnets
     - ECS Fargate tasks in private subnets

## ⏸️ BLOCKED - AWS SSO Credentials

**Issue**: AWS SSO tokens expire frequently and must be refreshed manually.

**Current Status**: Terraform plan is ready to run but blocked by expired credentials.

**Next Steps**:
1. Refresh AWS SSO credentials: `aws sso login`
2. Run Terraform apply:
   ```bash
   cd terraform/environments/staging
   terraform apply -var="db_password=YOUR_PASSWORD" -var="domain_name=adcp-salesagent.com"
   ```

## 📋 PENDING TASKS

### 1. Apply Terraform Configuration
Once credentials are refreshed, Terraform will create:
- **ALB**: Application Load Balancer with 3 target groups
- **RDS**: PostgreSQL database (db.t4g.micro, 20GB)
- **ECS**: Fargate cluster with 1 service (0.5 vCPU, 1GB RAM)
- **Secrets**: 3 AWS Secrets Manager secrets
- **Security Groups**: ALB, ECS, and RDS security groups

**Estimated Monthly Cost**: ~$45-50
- RDS db.t4g.micro: ~$15
- ECS Fargate (0.5 vCPU, 1GB): ~$15
- ALB: ~$18
- Data transfer: ~$2-5
- **Savings**: ~$40/month by reusing Newton's network infrastructure

### 2. DNS Configuration
After Terraform creates the ALB, configure DNS:
```bash
# Get ALB DNS name
terraform output alb_dns_name

# Create CNAME records:
mcp-espn.adcp-salesagent.com  -> [ALB-DNS-NAME]
mcp-cnn.adcp-salesagent.com   -> [ALB-DNS-NAME]
mcp-nyt.adcp-salesagent.com   -> [ALB-DNS-NAME]
admin-espn.adcp-salesagent.com -> [ALB-DNS-NAME]
admin-cnn.adcp-salesagent.com  -> [ALB-DNS-NAME]
admin-nyt.adcp-salesagent.com  -> [ALB-DNS-NAME]
a2a-espn.adcp-salesagent.com   -> [ALB-DNS-NAME]
a2a-cnn.adcp-salesagent.com    -> [ALB-DNS-NAME]
a2a-nyt.adcp-salesagent.com    -> [ALB-DNS-NAME]
```

### 3. ECS Task Definition Refinement
Current task definition uses a simple approach (git clone + setup script).

**Improvements needed**:
- Build and push Docker image to ECR
- Use proper health checks
- Implement graceful shutdown
- Add CloudWatch logs and metrics
- Configure auto-scaling

### 4. Database Initialization
After RDS is created, run initialization:
```bash
# Get database endpoint
terraform output database_endpoint

# Run migrations and populate demo data
# (Need to adapt start_demo_agents.sh for AWS environment)
```

### 5. Newton Integration
Update Newton's MCP client configuration to use AWS endpoints:
```json
{
  "espn_sales_agent": {
    "url": "http://mcp-espn.adcp-salesagent.com/mcp/",
    "auth": {"type": "bearer", "token": "..."}
  },
  "cnn_sales_agent": {
    "url": "http://mcp-cnn.adcp-salesagent.com/mcp/",
    "auth": {"type": "bearer", "token": "..."}
  },
  "nyt_sales_agent": {
    "url": "http://mcp-nyt.adcp-salesagent.com/mcp/",
    "auth": {"type": "bearer", "token": "..."}
  }
}
```

## 🔧 TECHNICAL DECISIONS

### Why Fargate vs EC2?
- **Serverless**: No server management
- **Auto-scaling**: Built-in horizontal scaling
- **Cost-effective**: Pay only for what you use
- **Multi-AZ**: High availability by default

### Why Reuse Newton's VPC?
- **Cost savings**: ~$40/month (NAT Gateway + VPC costs)
- **Network efficiency**: Low-latency communication between Newton and sales agents
- **Simplified architecture**: One network to manage

### Why Application Load Balancer?
- **Path-based routing**: Route by hostname (espn/cnn/nyt subdomains)
- **Health checks**: Automatic unhealthy task replacement
- **SSL termination**: Can add HTTPS in the future
- **Auto-scaling integration**: Works seamlessly with ECS

## 📁 FILE STRUCTURE

```
terraform/
├── modules/
│   ├── alb/
│   │   ├── main.tf (ALB, target groups, listeners)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   └── main.tf (RDS, security groups, IAM)
│   ├── ecs/
│   │   ├── main.tf (Cluster, task definition, service)
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── networking/
│       └── main.tf (VPC, subnets, gateways - NOT USED, reusing Newton's)
├── environments/
│   └── staging/
│       ├── main.tf (Root configuration)
│       └── terraform.tfvars (Actual values - GITIGNORED)
├── AWS_SETUP_GUIDE.md
├── NEWTON_VPC_REUSE.md
├── quick-start.sh
└── README.md
```

## 🚀 NEXT IMMEDIATE STEPS

1. **User refreshes AWS SSO credentials**:
   ```bash
   aws sso login
   ```

2. **Run Terraform apply**:
   ```bash
   cd /Users/danfinkel/github/opensource/salesagent/terraform/environments/staging
   terraform apply -var="db_password=YOUR_SECURE_PASSWORD" -var="domain_name=adcp-salesagent.com"
   ```

3. **Verify deployment**:
   ```bash
   # Check ECS service
   aws ecs describe-services --cluster salesagent-staging --services salesagent-staging
   
   # Check ALB health
   terraform output alb_dns_name
   curl http://[ALB-DNS-NAME]/health
   ```

4. **Test MCP endpoints**:
   ```bash
   curl http://mcp-espn.adcp-salesagent.com/health
   curl http://mcp-cnn.adcp-salesagent.com/health
   curl http://mcp-nyt.adcp-salesagent.com/health
   ```

## 💡 OPEN QUESTIONS

1. **Domain**: Is `adcp-salesagent.com` the correct domain? Do we need to purchase it?
2. **Authentication**: Should we enable authentication now or continue with test mode?
3. **Secrets**: Do you have actual Gemini/Google OAuth credentials to use, or use placeholders?
4. **Monitoring**: Do you want CloudWatch alarms set up (costs ~$0.10/alarm/month)?
5. **Backup**: Should we enable automated RDS backups (already configured, 7-day retention)?

---

**Status**: Infrastructure code is complete and ready to deploy. Waiting for user to refresh AWS SSO credentials to proceed.

