# AWS Migration Plan - Sales Agent AdCP Server

## Executive Summary

This plan outlines the strategy for migrating the AdCP sales agent from local development to AWS infrastructure, including proper repository management, identifying upstream-worthy changes, and setting up production-grade CI/CD.

---

## Part A: Repository Strategy

### Current State
- **Upstream**: `adcontextprotocol/salesagent` (open source reference implementation)
- **Local**: `/Users/danfinkel/github/opensource/salesagent` (direct clone)
- **Custom Work**: Newton integration, bug fixes, demo setup scripts

### Recommended Approach: Fork + Upstream Tracking

#### 1. Fork the Repository
```bash
# On GitHub.com
1. Navigate to: https://github.com/adcontextprotocol/salesagent
2. Click "Fork" → Create fork under your account (danfinkel/salesagent)
3. This creates: github.com/danfinkel/salesagent
```

#### 2. Reconfigure Local Repository
```bash
cd /Users/danfinkel/github/opensource/salesagent

# Add your fork as 'origin' (primary remote)
git remote rename origin upstream
git remote add origin git@github.com:danfinkel/salesagent.git

# Verify remotes
git remote -v
# Should show:
# origin     git@github.com:danfinkel/salesagent.git (fetch/push)
# upstream   https://github.com/adcontextprotocol/salesagent.git (fetch/push)
```

#### 3. Push Branches to Your Fork
```bash
# Push all your custom branches
git push -u origin main
git push -u origin backup/all-bug-fixes
git push -u origin fix/sqlalchemy-session-detachment
git push -u origin fix/suppress-gemini-warnings
git push -u origin feature/test-mode-auth-bypass

# Push demo infrastructure
git push -u origin demo/newton-integration  # Create this branch first
```

#### 4. Keep Upstream Synchronized
```bash
# Regularly sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

---

## Part B: Upstream Contribution Strategy

### Changes Suitable for Pull Requests to Open Source

#### ✅ **High Priority - Should PR Upstream**

**1. SQLAlchemy DetachedInstanceError Fix**
- **Branch**: `fix/sqlalchemy-session-detachment`
- **Why**: Critical bug fix affecting all deployments
- **Impact**: Fixes campaign creation failures during creative assignment
- **Risk**: Low - isolated change, well-tested
- **Action**: Create PR to `adcontextprotocol/salesagent:main`

**2. Suppress Gemini API Key Warnings**
- **Branch**: `fix/suppress-gemini-warnings`
- **Why**: Improves UX when Gemini is not configured (common case)
- **Impact**: Cleaner logs, less confusion
- **Risk**: Very low - only suppresses expected warnings
- **Action**: Create PR to `adcontextprotocol/salesagent:main`

#### ⚠️ **Maybe - Discuss with Maintainers**

**3. Mock Adapter Limits Increase (10M impressions, $10M budget)**
- **Current State**: Already in upstream main
- **Why**: More realistic testing limits
- **Action**: No PR needed - already upstream

#### ❌ **Should NOT PR Upstream**

**4. Test Mode Authentication Bypass**
- **Branch**: `feature/test-mode-auth-bypass`
- **Why**: Demo/testing feature, not production-ready
- **Risk**: Security concerns if misused
- **Action**: Keep in private fork only

**5. Newton Integration Scripts**
- **Files**: `scripts/demo/`, `docker-compose.testing.yml`, `NEWTON_*.md`
- **Why**: Specific to your Newton agent integration
- **Action**: Keep in private fork only

**6. Demo Infrastructure**
- **Files**: Multi-tenant setup scripts, demo data population
- **Why**: Useful reference but very specific to Newton demo
- **Action**: Could contribute as separate "examples" directory

### PR Preparation Checklist

For each upstream PR:

```markdown
- [ ] Branch rebased on latest upstream/main
- [ ] Tests pass locally (`./run_all_tests.sh ci`)
- [ ] Commit messages follow conventional format
- [ ] Detailed PR description with problem/solution
- [ ] No Newton-specific references in code
- [ ] Documentation updated if needed
- [ ] Pre-commit hooks pass
```

---

## Part C: Private Fork Organization

### Branch Strategy

```
main (synced with upstream)
├── production (AWS deployment target)
├── staging (AWS staging environment)
└── development (active development)
    ├── fix/* (bug fixes - may PR upstream)
    ├── feature/* (new features - usually private)
    └── demo/* (Newton integration - always private)
```

### Directory Structure for Custom Code

```
salesagent/ (your fork)
├── .github/
│   └── workflows/
│       ├── deploy-production.yml    # Deploy to AWS production
│       ├── deploy-staging.yml       # Deploy to AWS staging
│       └── test.yml                 # Run tests on PRs
├── docs/
│   └── custom/
│       ├── newton-integration.md    # Your custom docs
│       └── aws-deployment.md        # AWS-specific docs
├── scripts/
│   ├── demo/                        # Newton demo scripts
│   ├── aws/                         # AWS deployment scripts
│   └── setup/                       # Custom setup scripts
├── terraform/                       # Infrastructure as Code (NEW)
│   ├── modules/
│   │   ├── ecs/
│   │   ├── rds/
│   │   └── networking/
│   ├── environments/
│   │   ├── staging/
│   │   └── production/
│   └── backend.tf
└── docker-compose.testing.yml       # Custom test config
```

---

## Part D: AWS Architecture

### Recommended AWS Services

#### 1. **Compute: Amazon ECS with Fargate** (Serverless Containers)
- **Why**: Managed container orchestration, no EC2 management
- **Cost**: ~$50-150/month per environment (staging/prod)
- **Alternatives**: 
  - AWS App Runner (simpler, less control)
  - EKS (overkill for 3 services)
  - EC2 (more ops overhead)

#### 2. **Database: Amazon RDS PostgreSQL**
- **Why**: Managed PostgreSQL, automated backups, scaling
- **Instance**: db.t4g.micro (staging) / db.t4g.small (production)
- **Cost**: ~$15-50/month depending on size
- **Features**: Multi-AZ for production, automated backups

#### 3. **Secrets: AWS Secrets Manager**
- **Why**: Secure credential storage, rotation, audit logs
- **Cost**: $0.40/secret/month + $0.05/10k API calls
- **Secrets**:
  - Database credentials
  - Gemini API key
  - Google OAuth credentials
  - GAM OAuth credentials

#### 4. **Load Balancer: Application Load Balancer (ALB)**
- **Why**: SSL termination, health checks, multi-service routing
- **Cost**: ~$22/month + $0.008/GB data processed
- **Features**: Route by path to different services (MCP, Admin, A2A)

#### 5. **Monitoring: CloudWatch**
- **Why**: Built-in AWS integration, logs, metrics, alarms
- **Cost**: ~$5-20/month for typical usage
- **Features**: Log aggregation, dashboards, alerting

#### 6. **Networking: VPC with Public/Private Subnets**
- **Why**: Network isolation, security
- **Cost**: Free (except NAT gateway ~$32/month if needed)
- **Design**: Public subnets for ALB, private for ECS + RDS

### Architecture Diagram

```
┌─────────────────── AWS VPC ───────────────────┐
│                                                │
│  ┌──────────────── Public Subnet ──────────┐  │
│  │                                          │  │
│  │   ┌─── Application Load Balancer ───┐   │  │
│  │   │  SSL (*.yourdomain.com)         │   │  │
│  │   │  - /mcp/*     → MCP Service     │   │  │
│  │   │  - /admin/*   → Admin UI        │   │  │
│  │   │  - /a2a/*     → A2A Server      │   │  │
│  │   └─────────────────────────────────┘   │  │
│  └──────────────────────────────────────────┘  │
│                        │                        │
│  ┌──────────────── Private Subnet ──────────┐  │
│  │                   │                       │  │
│  │   ┌─── ECS Fargate Cluster ───┐          │  │
│  │   │                            │          │  │
│  │   │  ┌──── Task Definition ─┐ │          │  │
│  │   │  │  MCP Server :8080    │ │          │  │
│  │   │  │  Admin UI :8001      │ │          │  │
│  │   │  │  A2A Server :8091    │ │          │  │
│  │   │  └──────────────────────┘ │          │  │
│  │   │                            │          │  │
│  │   │  Auto-scaling:             │          │  │
│  │   │  Min: 1, Max: 5 tasks      │          │  │
│  │   └────────────────────────────┘          │  │
│  │                   │                       │  │
│  │   ┌─── RDS PostgreSQL ───┐               │  │
│  │   │  db.t4g.small        │               │  │
│  │   │  Multi-AZ (prod)     │               │  │
│  │   │  Encrypted           │               │  │
│  │   └──────────────────────┘               │  │
│  └──────────────────────────────────────────┘  │
│                                                │
└────────────────────────────────────────────────┘
```

### Multi-Tenant AWS Strategy

#### Option 1: Single Deployment, Multiple Tenants (Recommended)
- **Design**: One ECS cluster, one database, tenant separation via data isolation
- **Cost**: Most economical (~$100/month total)
- **Use Case**: ESPN, CNN, NYT as tenants in one system
- **Pros**: Simple, matches current architecture
- **Cons**: All tenants share resources

#### Option 2: Separate Deployments per Tenant
- **Design**: ESPN, CNN, NYT each get own ECS cluster + database
- **Cost**: Higher (~$100/month per tenant)
- **Use Case**: Complete isolation required
- **Pros**: True multi-tenancy, independent scaling
- **Cons**: More complex, expensive

**Recommendation**: Start with Option 1 (single deployment), scale to Option 2 if needed.

---

## Part E: GitHub Actions CI/CD Pipeline

### Workflow Files

#### 1. **Test on Pull Request** (`.github/workflows/test.yml`)
```yaml
name: Test

on:
  pull_request:
    branches: [main, staging, production]
  push:
    branches: [main, staging, production]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
        run: |
          uv run pytest tests/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### 2. **Deploy to Staging** (`.github/workflows/deploy-staging.yml`)
```yaml
name: Deploy Staging

on:
  push:
    branches: [staging]
  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: salesagent-staging
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster salesagent-staging \
            --service salesagent-staging-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster salesagent-staging \
            --services salesagent-staging-service
      
      - name: Run database migrations
        run: |
          # Execute migrations via ECS task
          aws ecs run-task \
            --cluster salesagent-staging \
            --task-definition salesagent-migration-staging \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

#### 3. **Deploy to Production** (`.github/workflows/deploy-production.yml`)
```yaml
name: Deploy Production

on:
  push:
    branches: [production]
  workflow_dispatch:  # Manual trigger with approval

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval in GitHub
    
    steps:
      # Similar to staging but with production resources
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: salesagent-production
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster salesagent-production \
            --service salesagent-production-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster salesagent-production \
            --services salesagent-production-service
      
      - name: Run smoke tests
        run: |
          curl -f https://api.yourdomain.com/health || exit 1
      
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "✅ Production deployment successful",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Deployment*\nCommit: ${{ github.sha }}\nStatus: Success ✅"
                  }
                }
              ]
            }
```

### GitHub Secrets to Configure

In your GitHub repository settings (Settings → Secrets → Actions):

```
AWS_ACCESS_KEY_ID              # IAM user with ECS/ECR permissions
AWS_SECRET_ACCESS_KEY          # IAM secret key
GEMINI_API_KEY                 # Gemini API key
GOOGLE_CLIENT_ID               # OAuth client ID
GOOGLE_CLIENT_SECRET           # OAuth secret
SUPER_ADMIN_EMAILS             # Admin emails
SLACK_WEBHOOK_URL              # Optional: deployment notifications
```

---

## Part F: Terraform Infrastructure as Code

### Directory Structure

```
terraform/
├── modules/
│   ├── ecs/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── rds/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── networking/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
└── backend.tf
```

### Sample Terraform Config

#### `terraform/environments/staging/main.tf`
```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "yourcompany-terraform-state"
    key    = "salesagent/staging/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = "us-east-1"
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "salesagent"
      ManagedBy   = "terraform"
    }
  }
}

module "networking" {
  source = "../../modules/networking"
  
  environment = "staging"
  vpc_cidr    = "10.0.0.0/16"
}

module "rds" {
  source = "../../modules/rds"
  
  environment        = "staging"
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  instance_class     = "db.t4g.micro"
  allocated_storage  = 20
}

module "ecs" {
  source = "../../modules/ecs"
  
  environment        = "staging"
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids
  
  database_url = module.rds.connection_url
  
  container_image = "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest"
  
  secrets = {
    GEMINI_API_KEY       = "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:staging/gemini-key"
    GOOGLE_CLIENT_ID     = "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:staging/google-client-id"
    GOOGLE_CLIENT_SECRET = "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:staging/google-secret"
  }
}

output "alb_dns_name" {
  value = module.ecs.alb_dns_name
}

output "database_endpoint" {
  value     = module.rds.endpoint
  sensitive = true
}
```

### Terraform Module: ECS (`terraform/modules/ecs/main.tf` - Abbreviated)
```hcl
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-salesagent-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "salesagent" {
  family                   = "${var.environment}-salesagent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name  = "mcp-server"
      image = var.container_image
      
      portMappings = [
        { containerPort = 8080, protocol = "tcp" },
        { containerPort = 8001, protocol = "tcp" },
        { containerPort = 8091, protocol = "tcp" }
      ]
      
      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "DATABASE_URL", value = var.database_url }
      ]
      
      secrets = [
        for key, arn in var.secrets : {
          name      = key
          valueFrom = arn
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.environment}/salesagent"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "salesagent" {
  name            = "${var.environment}-salesagent-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.salesagent.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.mcp.arn
    container_name   = "mcp-server"
    container_port   = 8080
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.admin.arn
    container_name   = "mcp-server"
    container_port   = 8001
  }
  
  depends_on = [aws_lb_listener.https]
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.environment}-salesagent-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids
}

# Target groups for each service
resource "aws_lb_target_group" "mcp" {
  name        = "${var.environment}-mcp-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

resource "aws_lb_target_group" "admin" {
  name        = "${var.environment}-admin-tg"
  port        = 8001
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    path = "/health"
  }
}

# Listener rules for path-based routing
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp.arn
  }
}

resource "aws_lb_listener_rule" "admin" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100
  
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.admin.arn
  }
  
  condition {
    path_pattern {
      values = ["/admin/*"]
    }
  }
}

# Security Groups
resource "aws_security_group" "ecs_tasks" {
  name   = "${var.environment}-ecs-tasks-sg"
  vpc_id = var.vpc_id
  
  ingress {
    from_port       = 8080
    to_port         = 8091
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "alb" {
  name   = "${var.environment}-alb-sg"
  vpc_id = var.vpc_id
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

## Part G: Configuration Management

### Environment Variables Strategy

#### 1. **Build-time Config** (baked into Docker image)
```dockerfile
# Dockerfile
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1
```

#### 2. **Deploy-time Config** (set in ECS task definition)
```json
{
  "environment": [
    {"name": "DATABASE_URL", "value": "postgresql://..."},
    {"name": "ENVIRONMENT", "value": "production"}
  ]
}
```

#### 3. **Runtime Secrets** (fetched from Secrets Manager)
```json
{
  "secrets": [
    {"name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
    {"name": "GOOGLE_CLIENT_SECRET", "valueFrom": "arn:aws:secretsmanager:..."}
  ]
}
```

### Secrets Management Workflow

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name staging/gemini-api-key \
  --secret-string "your-api-key"

aws secretsmanager create-secret \
  --name staging/google-oauth \
  --secret-string '{"client_id":"...","client_secret":"..."}'

# Rotate secrets (best practice)
aws secretsmanager rotate-secret \
  --secret-id staging/google-oauth \
  --rotation-lambda-arn arn:aws:lambda:...
```

---

## Part H: Testing Strategy

### Local Testing (Before AWS Deploy)
```bash
# 1. Test with local Docker Compose
docker-compose -f docker-compose.testing.yml up

# 2. Run full test suite
./run_all_tests.sh ci

# 3. Test migrations
uv run python migrate.py

# 4. Verify health endpoints
curl http://localhost:9580/health
curl http://localhost:9501/health
```

### Staging Environment Testing
```bash
# 1. Deploy to staging via GitHub Actions
git push origin staging

# 2. Run smoke tests against staging
curl -f https://staging.yourdomain.com/health

# 3. Test MCP tools
# Use Newton to connect to staging MCP server

# 4. Test multi-tenant isolation
# Create test campaigns for ESPN/CNN/NYT tenants
```

### Production Deployment Checklist
```markdown
- [ ] All tests pass on staging
- [ ] Database migrations tested on staging
- [ ] Load testing completed (if applicable)
- [ ] Rollback plan documented
- [ ] On-call engineer notified
- [ ] Monitoring dashboards reviewed
- [ ] Manual approval in GitHub Actions
- [ ] Post-deployment smoke tests pass
- [ ] Monitor error rates for 30 minutes
```

---

## Part I: Monitoring & Alerting

### CloudWatch Dashboards

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "ECS Service CPU/Memory",
        "metrics": [
          ["AWS/ECS", "CPUUtilization", {"stat": "Average"}],
          ["AWS/ECS", "MemoryUtilization", {"stat": "Average"}]
        ]
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "RDS Database Connections",
        "metrics": [
          ["AWS/RDS", "DatabaseConnections"]
        ]
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20",
        "region": "us-east-1",
        "title": "Recent Errors"
      }
    }
  ]
}
```

### CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.environment}-salesagent-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  
  alarm_actions = [aws_sns_topic.alerts.arn]
  
  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.salesagent.name
  }
}

resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-salesagent-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

### Log Aggregation

```python
# Add structured logging to the application
import structlog

logger = structlog.get_logger()

# CloudWatch will automatically parse JSON logs
logger.info(
    "media_buy_created",
    tenant_id=tenant_id,
    media_buy_id=media_buy_id,
    principal_id=principal_id,
    budget=total_budget,
)
```

---

## Part J: Security Considerations

### IAM Roles

```hcl
# ECS Task Execution Role (pulls secrets, writes logs)
resource "aws_iam_role" "ecs_execution" {
  name = "${var.environment}-ecs-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Secrets Manager access
resource "aws_iam_role_policy" "secrets_access" {
  role = aws_iam_role.ecs_execution.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = [
        "arn:aws:secretsmanager:us-east-1:*:secret:${var.environment}/*"
      ]
    }]
  })
}

# ECS Task Role (application permissions)
resource "aws_iam_role" "ecs_task" {
  name = "${var.environment}-ecs-task-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

# Add application-specific permissions here (S3, SES, etc.)
```

### Database Security

```hcl
resource "aws_db_instance" "main" {
  # ... other config ...
  
  # Security
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.db.arn
  
  # Network
  publicly_accessible = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  # Backup
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
}

resource "aws_security_group" "rds" {
  name   = "${var.environment}-rds-sg"
  vpc_id = var.vpc_id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "Allow PostgreSQL from ECS tasks only"
  }
}
```

### SSL/TLS Certificates

```hcl
# Use AWS Certificate Manager for free SSL certs
resource "aws_acm_certificate" "main" {
  domain_name               = "*.yourdomain.com"
  subject_alternative_names = ["yourdomain.com"]
  validation_method         = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
}

# Validate via Route53
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  
  zone_id = var.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}
```

---

## Part K: Cost Optimization

### Estimated Monthly Costs

#### Staging Environment
```
ECS Fargate (1 task, 1 vCPU, 2GB)      ~$30/month
RDS PostgreSQL (db.t4g.micro)          ~$15/month
Application Load Balancer              ~$22/month
CloudWatch (logs + metrics)            ~$10/month
Secrets Manager (5 secrets)            ~$2/month
Data Transfer                          ~$5/month
---------------------------------------------
TOTAL STAGING:                         ~$84/month
```

#### Production Environment
```
ECS Fargate (2 tasks, 1 vCPU, 2GB)     ~$60/month
RDS PostgreSQL (db.t4g.small, Multi-AZ) ~$65/month
Application Load Balancer               ~$22/month
CloudWatch (logs + metrics)             ~$20/month
Secrets Manager (5 secrets)             ~$2/month
Data Transfer                           ~$15/month
CloudFront (optional CDN)               ~$10/month
---------------------------------------------
TOTAL PRODUCTION:                       ~$194/month
```

**Grand Total (Staging + Production): ~$280/month**

### Cost Savings Strategies

1. **Use Fargate Spot** (up to 70% savings)
```hcl
capacity_provider_strategy {
  capacity_provider = "FARGATE_SPOT"
  weight            = 1
  base              = 0
}
```

2. **Reserved Instances for RDS** (up to 40% savings)
```bash
# For predictable long-term workloads
aws rds purchase-reserved-db-instances-offering \
  --reserved-db-instances-offering-id xxx \
  --reserved-db-instance-id salesagent-prod-ri
```

3. **S3 Lifecycle Policies** (for logs)
```hcl
resource "aws_s3_bucket_lifecycle_rule" "logs" {
  bucket = aws_s3_bucket.logs.id
  enabled = true
  
  transition {
    days          = 30
    storage_class = "STANDARD_IA"
  }
  
  transition {
    days          = 90
    storage_class = "GLACIER"
  }
  
  expiration {
    days = 365
  }
}
```

4. **Auto-scaling Down During Off-Hours**
```hcl
resource "aws_appautoscaling_scheduled_action" "scale_down_night" {
  name               = "scale-down-night"
  service_namespace  = "ecs"
  resource_id        = "service/${var.cluster_name}/${var.service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  schedule           = "cron(0 22 * * ? *)"  # 10 PM UTC
  
  scalable_target_action {
    min_capacity = 1
    max_capacity = 1
  }
}

resource "aws_appautoscaling_scheduled_action" "scale_up_morning" {
  name               = "scale-up-morning"
  service_namespace  = "ecs"
  resource_id        = "service/${var.cluster_name}/${var.service_name}"
  scalable_dimension = "ecs:service:DesiredCount"
  schedule           = "cron(0 13 * * ? *)"  # 1 PM UTC (8 AM EST)
  
  scalable_target_action {
    min_capacity = 2
    max_capacity = 5
  }
}
```

---

## Part L: Migration Execution Plan

### Phase 1: Repository Setup (Week 1)
```bash
# Day 1: Fork and reorganize
1. Fork adcontextprotocol/salesagent to danfinkel/salesagent
2. Reconfigure local remotes (origin → danfinkel, upstream → adcontextprotocol)
3. Push all branches to your fork
4. Create production/staging branches

# Day 2-3: Upstream contributions
5. Create PRs for SQLAlchemy fix and Gemini warning suppression
6. Wait for upstream review/merge

# Day 4-5: Infrastructure code
7. Create terraform/ directory structure
8. Write Terraform modules for networking, RDS, ECS
9. Test Terraform plan locally (terraform plan)
```

### Phase 2: AWS Infrastructure (Week 2)
```bash
# Day 1: AWS account setup
1. Create/configure AWS account
2. Set up AWS CLI and credentials
3. Create S3 bucket for Terraform state

# Day 2-3: Deploy staging infrastructure
4. cd terraform/environments/staging
5. terraform init
6. terraform plan
7. terraform apply (creates VPC, RDS, ECS cluster)

# Day 4-5: Configure services
8. Store secrets in Secrets Manager
9. Set up CloudWatch dashboards
10. Test database connectivity
```

### Phase 3: CI/CD Setup (Week 3)
```bash
# Day 1-2: GitHub Actions
1. Create .github/workflows/*.yml files
2. Configure GitHub secrets
3. Test CI pipeline with dummy deployment

# Day 3-4: First deployment
4. Push to staging branch
5. Watch GitHub Actions deploy to AWS
6. Debug any issues

# Day 5: Validation
7. Run smoke tests against staging
8. Test Newton → staging connection
9. Verify multi-tenant isolation
```

### Phase 4: Production Deployment (Week 4)
```bash
# Day 1-2: Production infrastructure
1. cd terraform/environments/production
2. terraform plan
3. terraform apply
4. Configure production secrets

# Day 3: Deploy to production
5. Merge staging → production
6. GitHub Actions deploys automatically
7. Monitor CloudWatch metrics

# Day 4-5: Validation & handoff
8. Run full integration tests
9. Document runbooks for operations
10. Train team on AWS console
```

---

## Part M: Rollback Procedures

### Automated Rollback (GitHub Actions)
```yaml
- name: Health check
  id: health_check
  run: |
    for i in {1..5}; do
      if curl -f https://api.yourdomain.com/health; then
        echo "Health check passed"
        exit 0
      fi
      echo "Attempt $i failed, retrying..."
      sleep 10
    done
    echo "Health check failed after 5 attempts"
    exit 1

- name: Rollback on failure
  if: failure()
  run: |
    # Get previous task definition
    PREV_TASK_DEF=$(aws ecs describe-services \
      --cluster salesagent-production \
      --services salesagent-production-service \
      --query 'services[0].deployments[?status==`ACTIVE`].taskDefinition' \
      --output text | head -2 | tail -1)
    
    # Rollback to previous
    aws ecs update-service \
      --cluster salesagent-production \
      --service salesagent-production-service \
      --task-definition $PREV_TASK_DEF
```

### Manual Rollback
```bash
# List recent task definitions
aws ecs list-task-definitions \
  --family-prefix production-salesagent \
  --sort DESC

# Rollback to specific version
aws ecs update-service \
  --cluster salesagent-production \
  --service salesagent-production-service \
  --task-definition production-salesagent:42
```

---

## Part N: Next Steps & Action Items

### Immediate Actions (This Week)
- [ ] Fork `adcontextprotocol/salesagent` on GitHub
- [ ] Reconfigure local repository remotes
- [ ] Push branches to your fork (backup/all-bug-fixes, fix/*, feature/*)
- [ ] Create PRs for upstream contributions (SQLAlchemy, Gemini warnings)
- [ ] Decide on AWS region (recommend us-east-1 for lowest cost)

### Short Term (Next 2 Weeks)
- [ ] Set up AWS account (if not already)
- [ ] Create Terraform configuration for staging
- [ ] Deploy staging infrastructure to AWS
- [ ] Configure GitHub Actions for CI/CD
- [ ] Test Newton → AWS staging connection

### Medium Term (Next Month)
- [ ] Deploy production infrastructure
- [ ] Set up monitoring and alerting
- [ ] Document operational runbooks
- [ ] Train team on AWS deployment
- [ ] Consider multi-region deployment (if needed)

### Long Term Considerations
- [ ] Multi-region deployment for high availability
- [ ] CDN integration (CloudFront) for static assets
- [ ] Database read replicas for scaling
- [ ] Advanced monitoring (Datadog, New Relic)
- [ ] Cost optimization review (Reserved Instances, Spot)

---

## Appendix A: Useful Commands

### Docker
```bash
# Build and tag for ECR
docker build -t salesagent:latest .
docker tag salesagent:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/salesagent:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/salesagent:latest
```

### AWS ECS
```bash
# View service status
aws ecs describe-services \
  --cluster salesagent-production \
  --services salesagent-production-service

# View tasks
aws ecs list-tasks \
  --cluster salesagent-production \
  --service-name salesagent-production-service

# View logs
aws logs tail /ecs/production/salesagent --follow

# Execute command in running task
aws ecs execute-command \
  --cluster salesagent-production \
  --task TASK_ID \
  --container mcp-server \
  --interactive \
  --command "/bin/bash"
```

### Terraform
```bash
# Initialize
terraform init

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# Destroy (careful!)
terraform destroy

# View state
terraform show
terraform state list

# Import existing resource
terraform import aws_ecs_cluster.main arn:aws:ecs:us-east-1:ACCOUNT:cluster/NAME
```

### Database Migrations
```bash
# Run migrations via ECS task
aws ecs run-task \
  --cluster salesagent-production \
  --task-definition salesagent-migration \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}" \
  --overrides '{
    "containerOverrides": [{
      "name": "mcp-server",
      "command": ["python", "migrate.py"]
    }]
  }'
```

---

## Appendix B: Troubleshooting Guide

### Issue: ECS Tasks Fail to Start
```bash
# Check task definition
aws ecs describe-task-definition --task-definition production-salesagent:latest

# Check service events
aws ecs describe-services \
  --cluster salesagent-production \
  --services salesagent-production-service \
  --query 'services[0].events[:10]'

# Common causes:
# - Image pull failures → Check ECR permissions
# - Health check failures → Verify /health endpoint
# - Resource limits → Increase CPU/memory
# - Secrets access → Check IAM role
```

### Issue: Database Connection Failures
```bash
# Test connectivity from ECS task
aws ecs execute-command \
  --cluster salesagent-production \
  --task TASK_ID \
  --container mcp-server \
  --interactive \
  --command "pg_isready -h DB_HOST -p 5432"

# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxx

# Verify RDS status
aws rds describe-db-instances \
  --db-instance-identifier salesagent-production
```

### Issue: High Costs
```bash
# Analyze costs by service
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --group-by Type=SERVICE

# Check most expensive resources
# Look for: Fargate tasks left running, unused NAT gateways, large RDS instances
```

---

## Summary

This migration plan provides a comprehensive roadmap for moving your AdCP sales agent from local development to production AWS infrastructure. Key highlights:

1. **Fork Strategy**: Maintain private fork while contributing bug fixes upstream
2. **AWS Architecture**: ECS Fargate + RDS PostgreSQL + ALB for ~$280/month
3. **CI/CD**: GitHub Actions with automated testing and deployment
4. **Infrastructure as Code**: Terraform for reproducible environments
5. **Security**: Secrets Manager, IAM roles, encrypted storage
6. **Monitoring**: CloudWatch dashboards, alarms, structured logging

**Estimated Timeline**: 4 weeks for full migration (staging + production)
**Estimated Cost**: $84/month (staging) + $194/month (production) = $278/month total

**Next Immediate Step**: Fork the repository on GitHub and start writing Terraform configuration for staging environment.

---

## Questions & Clarifications Needed

1. **Domain Name**: Do you have a domain for hosting? (e.g., `adcp.yourdomain.com`)
2. **AWS Region**: Preference? (us-east-1 recommended for cost)
3. **Upstream PRs**: Should I create the PRs now for the bug fixes?
4. **Newton Integration**: Will Newton connect to AWS deployment or stay local?
5. **Budget**: Is ~$280/month acceptable for AWS costs?
6. **Team**: Who will manage AWS infrastructure ongoing?

Let me know if you'd like me to:
- Create the Terraform configuration files
- Write the GitHub Actions workflows
- Start the repository fork process
- Create upstream PRs for bug fixes
- Clarify or expand any section

This plan is comprehensive but flexible - we can adjust based on your specific needs and constraints!

