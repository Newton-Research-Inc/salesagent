# AWS Infrastructure Setup Guide - Newton Demo

Complete guide to deploying the Newton demo (ESPN/CNN/NYT sales agents) to AWS.

---

## 🎯 What We're Building

```
AWS Staging Environment
├── VPC with public/private subnets
├── RDS PostgreSQL (shared database)
├── Application Load Balancer
│   ├── espn.demo.yourdomain.com → ESPN ECS Service
│   ├── cnn.demo.yourdomain.com → CNN ECS Service
│   └── nyt.demo.yourdomain.com → NYT ECS Service
└── ECS Fargate (3 separate services)
```

**Estimated Cost**: ~$92/month for staging
git push origin staging
---

## 📋 Prerequisites

### 1. AWS Account
- Active AWS account
- Billing configured
- Credit card on file

### 2. Domain Name
You need a domain for the demo agents. Options:
- **Buy new**: AWS Route53 (~$12/year for .com)
- **Use existing**: Any domain, transfer DNS to Route53

### 3. Local Tools
```bash
# Install AWS CLI
brew install awscli  # macOS
# OR: pip install awscli

# Install Terraform
brew install terraform  # macOS
# OR: https://www.terraform.io/downloads

# Verify installations
aws --version
terraform --version
```

---

## 🚀 Phase 1: AWS Account Setup (10 minutes)

### Step 1.1: Create IAM User for Deployments

1. **Go to AWS Console** → IAM → Users → Create User

2. **User details**:
   - Username: `salesagent-deploy`
   - Access type: ☑ Programmatic access

3. **Attach policies**:
   - `AmazonEC2ContainerRegistryPowerUser`
   - `AmazonECSFullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonVPCFullAccess`
   - `ElasticLoadBalancingFullAccess`
   - `IAMFullAccess`
   - `AmazonRoute53FullAccess`
   - `AWSCertificateManagerFullAccess`

4. **Save credentials**:
   - Access Key ID: `AKIAXXXXXXXXXXXXXXXX`
   - Secret Access Key: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 1.2: Configure AWS CLI

```bash
aws configure
# AWS Access Key ID: [paste from above]
# AWS Secret Access Key: [paste from above]
# Default region name: us-east-1
# Default output format: json

# Verify
aws sts get-caller-identity
```

### Step 1.3: Create S3 Bucket for Terraform State

```bash
# Create bucket (must be globally unique)
aws s3 mb s3://salesagent-demo-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket salesagent-demo-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket salesagent-demo-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## 🏗️ Phase 2: Terraform Infrastructure (30 minutes)

### Step 2.1: Configure Variables

Create `terraform/environments/staging/terraform.tfvars`:

```hcl
aws_region  = "us-east-1"
environment = "staging"

# YOUR DOMAIN HERE
domain_name = "demo.yourdomain.com"

# Generate secure password
db_password = "CHANGE_THIS_SECURE_PASSWORD_123"
```

**⚠️ Important**: 
- Replace `demo.yourdomain.com` with your actual domain
- Generate a strong DB password: `openssl rand -base64 32`

### Step 2.2: Initialize Terraform

```bash
cd terraform/environments/staging

# Initialize (downloads providers)
terraform init

# Verify configuration
terraform validate
```

### Step 2.3: Plan Infrastructure

```bash
# See what will be created
terraform plan -out=tfplan

# Review the output carefully
# Should show:
# - VPC and subnets
# - RDS database
# - Load balancer
# - ECS cluster and services
# - ~40 resources total
```

### Step 2.4: Create Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# This takes ~10-15 minutes
# Watch for any errors
```

### Step 2.5: Save Outputs

```bash
# Get important URLs and values
terraform output > ../../../AWS_OUTPUTS.txt

# View outputs
terraform output
```

---

## 🌐 Phase 3: Domain & SSL Setup (15 minutes)

### Step 3.1: Get ALB DNS Name

```bash
terraform output alb_dns_name
# Example: staging-salesagent-alb-1234567890.us-east-1.elb.amazonaws.com
```

### Step 3.2: Create Route53 Hosted Zone (if needed)

If using a new domain or transferring DNS to AWS:

```bash
# Create hosted zone
aws route53 create-hosted-zone \
  --name demo.yourdomain.com \
  --caller-reference $(date +%s)

# Note the nameservers - update at your domain registrar
```

### Step 3.3: Create DNS Records

```bash
# Get hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name demo.yourdomain.com \
  --query "HostedZones[0].Id" \
  --output text | cut -d'/' -f3)

# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Create A records for each agent
for SUBDOMAIN in espn cnn nyt; do
  aws route53 change-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --change-batch '{
      "Changes": [{
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "'$SUBDOMAIN'.demo.yourdomain.com",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z35SXDOTRQ7X7K",
            "DNSName": "'$ALB_DNS'",
            "EvaluateTargetHealth": false
          }
        }
      }]
    }'
done
```

### Step 3.4: Request SSL Certificate

```bash
# Request certificate for all subdomains
aws acm request-certificate \
  --domain-name "*.demo.yourdomain.com" \
  --subject-alternative-names "demo.yourdomain.com" \
  --validation-method DNS \
  --region us-east-1

# Wait for validation email or DNS validation
# This can take 5-30 minutes
```

---

## 🐳 Phase 4: GitHub Actions CI/CD (20 minutes)

### Step 4.1: Configure GitHub Secrets

Go to: https://github.com/danf-newton/salesagent/settings/secrets/actions

Add these secrets:
- `AWS_ACCESS_KEY_ID` - From Step 1.1
- `AWS_SECRET_ACCESS_KEY` - From Step 1.1
- `AWS_REGION` - `us-east-1`
- `ECR_REPOSITORY` - From terraform output: `ecr_repository_url`
- `GEMINI_API_KEY` - Your Gemini API key (or dummy value)
- `DB_PASSWORD` - Same as in terraform.tfvars

### Step 4.2: Create GitHub Actions Workflow

I'll create the workflow file next...

### Step 4.3: Push and Deploy

```bash
# Go back to repo root
cd /Users/danfinkel/github/opensource/salesagent

# Checkout demo branch
git checkout demo/newton-integration

# Merge to staging
git checkout staging
git merge demo/newton-integration
git push origin staging

# This triggers GitHub Actions!
# Watch at: https://github.com/danf-newton/salesagent/actions
```

---

## 🗄️ Phase 5: Database Initialization (10 minutes)

### Step 5.1: Run Migrations

```bash
# Get database endpoint
DB_ENDPOINT=$(terraform output -raw database_endpoint)

# Connect via ECS task
aws ecs run-task \
  --cluster staging-salesagent-cluster \
  --task-definition salesagent-init \
  --launch-type FARGATE \
  --overrides '{
    "containerOverrides": [{
      "name": "init",
      "command": ["python", "migrate.py"]
    }]
  }'
```

### Step 5.2: Populate Demo Data

```bash
# Run demo data population
aws ecs run-task \
  --cluster staging-salesagent-cluster \
  --task-definition salesagent-init \
  --launch-type FARGATE \
  --overrides '{
    "containerOverrides": [{
      "name": "init",
      "command": ["bash", "scripts/demo/start_demo_agents.sh"]
    }]
  }'
```

---

## ✅ Phase 6: Testing & Validation

### Test 1: Health Checks

```bash
# Test each agent
curl https://espn.demo.yourdomain.com/health
curl https://cnn.demo.yourdomain.com/health
curl https://nyt.demo.yourdomain.com/health

# All should return: {"status": "healthy"}
```

### Test 2: MCP Endpoints

```bash
# Test ESPN MCP server
curl -X POST https://espn.demo.yourdomain.com/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# Should return list of available tools
```

### Test 3: Get Products

```bash
# Test get_products tool on ESPN
curl -X POST https://espn.demo.yourdomain.com/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"get_products",
      "arguments":{"brief":"sports advertising"}
    }
  }'

# Should return ESPN products
```

---

## 🔄 Phase 7: Update Newton Configuration

### Update Newton's DataConnector

Edit Newton's config to point to AWS:

**ESPN Agent**:
```json
{
  "name": "ESPN Sales Agent",
  "type": "mcp",
  "config": {
    "url": "https://espn.demo.yourdomain.com/mcp/",
    "headers": {
      "x-adcp-auth": "espn-demo-token"
    }
  }
}
```

**CNN Agent**:
```json
{
  "name": "CNN Sales Agent",
  "type": "mcp",
  "config": {
    "url": "https://cnn.demo.yourdomain.com/mcp/",
    "headers": {
      "x-adcp-auth": "cnn-demo-token"
    }
  }
}
```

**NYT Agent**:
```json
{
  "name": "NYT Sales Agent",
  "type": "mcp",
  "config": {
    "url": "https://nyt.demo.yourdomain.com/mcp/",
    "headers": {
      "x-adcp-auth": "nyt-demo-token"
    }
  }
}
```

### Test with Newton

Run a Newton conversation:
```
User: "I want to advertise Nike shoes to basketball fans during the NBA season"
Newton: [discovers ESPN, creates campaign...]
```

---

## 📊 Monitoring & Maintenance

### CloudWatch Logs

```bash
# View logs for ESPN agent
aws logs tail /ecs/staging/espn-agent --follow

# View logs for CNN agent
aws logs tail /ecs/staging/cnn-agent --follow

# View logs for NYT agent
aws logs tail /ecs/staging/nyt-agent --follow
```

### ECS Service Status

```bash
# Check all services
aws ecs list-services --cluster staging-salesagent-cluster

# Describe specific service
aws ecs describe-services \
  --cluster staging-salesagent-cluster \
  --services espn-agent-staging
```

### Database Monitoring

AWS Console → RDS → salesagent-staging-db → Monitoring

---

## 💰 Cost Breakdown

**Monthly Costs (Staging)**:
```
ECS Fargate (3 tasks × 0.5 vCPU × 1GB)    $40/month
RDS PostgreSQL (db.t4g.micro)              $15/month
Application Load Balancer                  $22/month
NAT Gateway                                $32/month
CloudWatch Logs                            $10/month
Data Transfer                              $5/month
Route53 Hosted Zone                        $0.50/month
────────────────────────────────────────────────────
Total:                                     ~$124/month
```

**Cost Savings**:
- Use Fargate Spot: Save ~70% on compute
- Shut down non-business hours: Save ~50% overall
- Single NAT Gateway (not 2): Save $32/month

---

## 🔧 Troubleshooting

### Issue: Tasks won't start
```bash
# Check task logs
aws ecs describe-tasks \
  --cluster staging-salesagent-cluster \
  --tasks TASK_ARN

# Common causes:
# - Image pull failures → Check ECR permissions
# - Database connection → Check security groups
# - Environment variables → Check task definition
```

### Issue: Domain not resolving
```bash
# Check DNS propagation
dig espn.demo.yourdomain.com

# Verify Route53 records
aws route53 list-resource-record-sets \
  --hosted-zone-id $ZONE_ID
```

### Issue: SSL certificate not validating
- Check validation emails
- Or add DNS records for validation
- Can take up to 30 minutes

---

## 🎉 Success Checklist

- [ ] AWS infrastructure deployed
- [ ] DNS configured and resolving
- [ ] SSL certificates issued
- [ ] All 3 agents responding to /health
- [ ] MCP endpoints working
- [ ] Demo data populated
- [ ] Newton can connect remotely
- [ ] Campaigns can be created

---

## 🚀 Next Steps

1. **Deploy to Production**: Repeat process with `terraform/environments/production`
2. **Set up monitoring**: CloudWatch dashboards + alarms
3. **Enable auto-scaling**: Scale based on CPU/memory
4. **Add backup automation**: RDS snapshots + S3
5. **Configure CI/CD**: Auto-deploy on push to production branch

---

## 📞 Support

- **Terraform issues**: Check `terraform/README.md`
- **AWS questions**: AWS Support or documentation
- **Application bugs**: Check CloudWatch logs

---

**Ready to deploy? Let's go!** 🚀

Start with Phase 1: AWS Account Setup

