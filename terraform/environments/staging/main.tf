# Staging Environment - Newton Demo Sales Agents
# REUSES Newton's existing VPC infrastructure (saves ~$40/month)

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # backend "s3" {
  #   bucket = "salesagent-demo-terraform-state-381492092437"
  #   key    = "staging/terraform.tfstate"
  #   region = "us-east-1"
  # }
  
  # Using local backend temporarily for SSO credentials
  # Uncomment S3 backend once credentials are stable
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "salesagent-demo"
      ManagedBy   = "terraform"
      Purpose     = "Newton MCP Demo"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "domain_name" {
  description = "Base domain for demo agents (e.g., demo.yourdomain.com)"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key for AI features"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "super_admin_emails" {
  description = "Super admin emails (comma-separated)"
  type        = string
  default     = "admin@example.com"
}

variable "existing_vpc_id" {
  description = "Existing VPC ID to reuse (Newton's dev-vpc)"
  type        = string
  default     = "vpc-0c3f93c08fc1d2530"
}

# Data Sources - Import Newton's existing infrastructure
data "aws_vpc" "newton" {
  id = var.existing_vpc_id  # Newton's dev-vpc
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.newton.id]
  }
  
  filter {
    name   = "tag:Name"
    values = ["dev-subnet-public*"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.newton.id]
  }
  
  filter {
    name   = "tag:Name"
    values = ["dev-subnet-private*"]
  }
}

data "aws_internet_gateway" "newton" {
  filter {
    name   = "attachment.vpc-id"
    values = [data.aws_vpc.newton.id]
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.environment}-salesagent-ecs-"
  description = "Security group for sales agent ECS tasks"
  vpc_id      = data.aws_vpc.newton.id
  
  # Allow inbound from ALB
  ingress {
    from_port       = 8080
    to_port         = 8091
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Allow traffic from ALB"
  }
  
  # Allow inbound from VPC (for Newton direct connections)
  ingress {
    from_port   = 9580
    to_port     = 9591
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.newton.cidr_block]
    description = "Allow direct MCP/Admin/A2A connections from Newton (VPC)"
  }
  
  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }
  
  tags = {
    Name = "${var.environment}-salesagent-ecs-sg"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "${var.environment}-salesagent-alb-"
  description = "Security group for sales agent ALB"
  vpc_id      = data.aws_vpc.newton.id
  
  # Allow HTTPS from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from internet"
  }
  
  # Allow HTTP from anywhere (for redirects)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from internet"
  }
  
  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }
  
  tags = {
    Name = "${var.environment}-salesagent-alb-sg"
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

# AWS Secrets Manager - Store sensitive credentials
resource "aws_secretsmanager_secret" "gemini_api_key" {
  name = "${var.environment}-salesagent-gemini-api-key"
  description = "Gemini API key for AI features"
  
  tags = {
    Name        = "${var.environment}-salesagent-gemini-api-key"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "gemini_api_key" {
  secret_id     = aws_secretsmanager_secret.gemini_api_key.id
  secret_string = var.gemini_api_key
}

resource "aws_secretsmanager_secret" "google_client_id" {
  name = "${var.environment}-salesagent-google-client-id"
  description = "Google OAuth client ID"
  
  tags = {
    Name        = "${var.environment}-salesagent-google-client-id"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "google_client_id" {
  secret_id     = aws_secretsmanager_secret.google_client_id.id
  secret_string = var.google_client_id
}

resource "aws_secretsmanager_secret" "google_client_secret" {
  name = "${var.environment}-salesagent-google-client-secret"
  description = "Google OAuth client secret"
  
  tags = {
    Name        = "${var.environment}-salesagent-google-client-secret"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "google_client_secret" {
  secret_id     = aws_secretsmanager_secret.google_client_secret.id
  secret_string = var.google_client_secret
}

# Database Module - Creates new RDS in Newton's VPC
module "database" {
  source = "../../modules/database"
  
  environment        = var.environment
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  db_password        = var.db_password
  instance_class     = "db.t4g.micro"
  allocated_storage  = 20
}

# Application Load Balancer Module
module "alb" {
  source = "../../modules/alb"
  
  environment       = var.environment
  vpc_id            = data.aws_vpc.newton.id
  public_subnet_ids = data.aws_subnets.public.ids
  alb_security_group_id = aws_security_group.alb.id
  domain_name       = var.domain_name
}

# ECS Module - ESPN Sales Agent (using existing salesagent-staging service)
module "ecs_espn" {
  source = "../../modules/ecs"
  
  environment        = "espn"  # Each tenant gets its own service name
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # ALB target groups (ESPN uses existing staging target groups)
  mcp_target_group_arn   = module.alb.mcp_target_group_arn
  admin_target_group_arn = module.alb.admin_target_group_arn
  a2a_target_group_arn   = module.alb.a2a_target_group_arn
  
  # Database connection (shared by all tenants)
  db_host     = split(":", module.database.endpoint)[0]
  db_name     = module.database.database_name
  db_username = module.database.username
  db_password = var.db_password
  
  # Secrets (from AWS Secrets Manager ARNs)
  gemini_api_key       = aws_secretsmanager_secret.gemini_api_key.arn
  google_client_id     = aws_secretsmanager_secret.google_client_id.arn
  google_client_secret = aws_secretsmanager_secret.google_client_secret.arn
  super_admin_emails   = var.super_admin_emails
  
  # Tenant-specific configuration
  tenant_id     = "espn"
  principal_id  = "nike"
  
  # ECR repository URL
  ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

# ECS Module - CNN Sales Agent
module "ecs_cnn" {
  source = "../../modules/ecs"
  
  environment        = "cnn"
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # ALB target groups (not actually used for MCP, only for admin/a2a if needed)
  mcp_target_group_arn   = module.alb.mcp_target_group_arn
  admin_target_group_arn = module.alb.admin_target_group_arn
  a2a_target_group_arn   = module.alb.a2a_target_group_arn
  
  # Database connection (shared by all tenants)
  db_host     = split(":", module.database.endpoint)[0]
  db_name     = module.database.database_name
  db_username = module.database.username
  db_password = var.db_password
  
  # Secrets
  gemini_api_key       = aws_secretsmanager_secret.gemini_api_key.arn
  google_client_id     = aws_secretsmanager_secret.google_client_id.arn
  google_client_secret = aws_secretsmanager_secret.google_client_secret.arn
  super_admin_emails   = var.super_admin_emails
  
  # Tenant-specific configuration
  tenant_id     = "cnn"
  principal_id  = "cocacola"
  
  # ECR repository URL
  ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

# ECS Module - NYT Sales Agent
module "ecs_nyt" {
  source = "../../modules/ecs"
  
  environment        = "nyt"
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # ALB target groups (not actually used for MCP, only for admin/a2a if needed)
  mcp_target_group_arn   = module.alb.mcp_target_group_arn
  admin_target_group_arn = module.alb.admin_target_group_arn
  a2a_target_group_arn   = module.alb.a2a_target_group_arn
  
  # Database connection (shared by all tenants)
  db_host     = split(":", module.database.endpoint)[0]
  db_name     = module.database.database_name
  db_username = module.database.username
  db_password = var.db_password
  
  # Secrets
  gemini_api_key       = aws_secretsmanager_secret.gemini_api_key.arn
  google_client_id     = aws_secretsmanager_secret.google_client_id.arn
  google_client_secret = aws_secretsmanager_secret.google_client_secret.arn
  super_admin_emails   = var.super_admin_emails
  
  # Tenant-specific configuration
  tenant_id     = "nyt"
  principal_id  = "apple"
  
  # ECR repository URL
  ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

# Outputs
output "vpc_info" {
  description = "Newton VPC information (reused)"
  value = {
    vpc_id     = data.aws_vpc.newton.id
    cidr_block = data.aws_vpc.newton.cidr_block
    note       = "Reusing Newton's existing VPC"
  }
}

output "network_cost_savings" {
  description = "Estimated monthly savings from reusing Newton's network"
  value       = "~$40/month saved (NAT Gateway + VPC costs)"
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.alb_dns_name
}

output "espn_url" {
  description = "ESPN agent URL"
  value       = "https://espn.${var.domain_name}"
}

output "cnn_url" {
  description = "CNN agent URL"
  value       = "https://cnn.${var.domain_name}"
}

output "nyt_url" {
  description = "NYT agent URL"
  value       = "https://nyt.${var.domain_name}"
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "ecs_clusters" {
  description = "ECS cluster information for all tenants"
  value = {
    espn = {
      cluster_id   = module.ecs_espn.cluster_id
      cluster_name = module.ecs_espn.cluster_name
      service_name = module.ecs_espn.service_name
    }
    cnn = {
      cluster_id   = module.ecs_cnn.cluster_id
      cluster_name = module.ecs_cnn.cluster_name
      service_name = module.ecs_cnn.service_name
    }
    nyt = {
      cluster_id   = module.ecs_nyt.cluster_id
      cluster_name = module.ecs_nyt.cluster_name
      service_name = module.ecs_nyt.service_name
    }
  }
}

output "next_steps" {
  description = "What to do next"
  value       = <<-EOT
    ✅ Multi-tenant sales agents deployed in Newton's VPC!
    
    Next steps:
    1. Get task IPs for Newton connection:
       ./scripts/get_task_ips.sh
    
    2. Configure Newton's MCP servers with task IPs:
       - ESPN: http://<espn-task-ip>:9580/mcp
       - CNN: http://<cnn-task-ip>:9580/mcp
       - NYT: http://<nyt-task-ip>:9580/mcp
    
    3. Test Newton's connection to each sales agent
    
    Cost: ~$90/month for 3 Fargate tasks (saved $40 by reusing Newton's network!)
    
    Note: MCP servers use direct VPC connection (no ALB needed)
  EOT
}
