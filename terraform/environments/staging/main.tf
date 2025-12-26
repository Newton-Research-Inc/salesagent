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

# Yahoo DSP Live API Credentials (optional - only needed for yahoo_live tenant)
variable "yahoo_dsp_client_id" {
  description = "Yahoo DSP OAuth Client ID (for yahoo_dsp_live adapter)"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "yahoo_dsp_client_secret" {
  description = "Yahoo DSP OAuth Client Secret (for yahoo_dsp_live adapter)"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "yahoo_dsp_seat_id" {
  description = "Yahoo DSP Seat ID (for yahoo_dsp_live adapter)"
  type        = string
  default     = "placeholder"
}

variable "yahoo_dsp_advertiser_id" {
  description = "Yahoo DSP Advertiser ID (for yahoo_dsp_live adapter)"
  type        = string
  default     = "placeholder"
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

# ============================================================================
# Service Discovery (shared across all tenants)
# ============================================================================
resource "aws_service_discovery_private_dns_namespace" "salesagent" {
  name        = "salesagent.local"
  vpc         = data.aws_vpc.newton.id
  description = "Private DNS namespace for AdCP Sales Agent service discovery"

  tags = {
    Name        = "salesagent-service-discovery"
    Environment = var.environment
  }
}

# ============================================================================
# Security Groups
# ============================================================================
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

# Yahoo DSP Live API Credentials (for yahoo_dsp_live adapter)
resource "aws_secretsmanager_secret" "yahoo_dsp_client_id" {
  name = "${var.environment}-salesagent-yahoo-dsp-client-id"
  description = "Yahoo DSP OAuth Client ID"
  
  tags = {
    Name        = "${var.environment}-salesagent-yahoo-dsp-client-id"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "yahoo_dsp_client_id" {
  secret_id     = aws_secretsmanager_secret.yahoo_dsp_client_id.id
  secret_string = var.yahoo_dsp_client_id
}

resource "aws_secretsmanager_secret" "yahoo_dsp_client_secret" {
  name = "${var.environment}-salesagent-yahoo-dsp-client-secret"
  description = "Yahoo DSP OAuth Client Secret"
  
  tags = {
    Name        = "${var.environment}-salesagent-yahoo-dsp-client-secret"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "yahoo_dsp_client_secret" {
  secret_id     = aws_secretsmanager_secret.yahoo_dsp_client_secret.id
  secret_string = var.yahoo_dsp_client_secret
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
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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

# ECS Module - Yahoo DSP (Programmatic Platform)
module "ecs_yahoo" {
  source = "../../modules/ecs"
  
  environment        = "yahoo"
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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
  tenant_id     = "yahoo"
  principal_id  = "nike"  # Shared principal (simulates Nike buying programmatically)
  
  # ECR repository URL
  ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

# ECS Module - NBCU (Linear + Streaming Broadcaster)
module "ecs_nbcu" {
  source = "../../modules/ecs"
  
  environment        = "nbcu"
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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
  tenant_id     = "nbcu"
  principal_id  = "honda_advertiser"  # Honda for cross-platform demo
  
  # ECR repository URL
  ecr_repository_url = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

# ECS Module - Yahoo DSP Live (Real API Integration)
module "ecs_yahoo_live" {
  source = "../../modules/ecs"
  
  environment        = "yahoo-live"
  vpc_id             = data.aws_vpc.newton.id
  private_subnet_ids = data.aws_subnets.private.ids
  ecs_security_group_id = aws_security_group.ecs_tasks.id
  
  # Service Discovery (shared namespace)
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.salesagent.id
  
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
  
  # Yahoo DSP Live specific secrets
  yahoo_dsp_client_id     = aws_secretsmanager_secret.yahoo_dsp_client_id.arn
  yahoo_dsp_client_secret = aws_secretsmanager_secret.yahoo_dsp_client_secret.arn
  yahoo_dsp_seat_id       = var.yahoo_dsp_seat_id
  yahoo_dsp_advertiser_id = var.yahoo_dsp_advertiser_id
  
  # TEST MODE ENABLED BY DEFAULT - Creates INACTIVE campaigns with max $5 budget
  # Change to "false" when ready for production use
  yahoo_dsp_test_mode     = "true"
  
  # Tool filtering - Only expose Yahoo DSP relevant tools
  # Core: get_products, create_media_buy, get_media_buy_delivery, etc.
  # Yahoo: listDeals, createCampaign, getCampaignDelivery, etc.
  enabled_tools = "core,yahoo"
  
  # Tenant-specific configuration
  tenant_id     = "yahoo_live"
  principal_id  = "yahoo_live_test_buyer"
  
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

output "yahoo_url" {
  description = "Yahoo DSP agent URL"
  value       = "https://yahoo.${var.domain_name}"
}

output "nbcu_url" {
  description = "NBCU agent URL"
  value       = "https://nbcu.${var.domain_name}"
}

output "yahoo_live_url" {
  description = "Yahoo DSP Live (Real API) agent URL"
  value       = "https://yahoo-live.${var.domain_name}"
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
    yahoo = {
      cluster_id   = module.ecs_yahoo.cluster_id
      cluster_name = module.ecs_yahoo.cluster_name
      service_name = module.ecs_yahoo.service_name
    }
    nbcu = {
      cluster_id   = module.ecs_nbcu.cluster_id
      cluster_name = module.ecs_nbcu.cluster_name
      service_name = module.ecs_nbcu.service_name
    }
    yahoo_live = {
      cluster_id   = module.ecs_yahoo_live.cluster_id
      cluster_name = module.ecs_yahoo_live.cluster_name
      service_name = module.ecs_yahoo_live.service_name
      note         = "Uses yahoo_dsp_live adapter (REAL Yahoo DSP API)"
    }
  }
}

output "service_discovery_dns" {
  description = "Service Discovery DNS names for each tenant"
  value = {
    espn       = module.ecs_espn.service_discovery_dns_name
    cnn        = module.ecs_cnn.service_discovery_dns_name
    nyt        = module.ecs_nyt.service_discovery_dns_name
    yahoo      = module.ecs_yahoo.service_discovery_dns_name
    nbcu       = module.ecs_nbcu.service_discovery_dns_name
    yahoo_live = module.ecs_yahoo_live.service_discovery_dns_name
  }
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker images"
  value       = "381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging"
}

output "next_steps" {
  description = "What to do next"
  value       = <<-EOT
    ✅ Multi-tenant sales agents deployed in Newton's VPC with Service Discovery!
    
    Next steps:
    1. Configure Newton's MCP servers with stable DNS names:
       - ESPN (Publisher): http://espn.salesagent.local:9580/mcp
       - CNN (Publisher): http://cnn.salesagent.local:9580/mcp
       - NYT (Publisher): http://nyt.salesagent.local:9580/mcp
       - Yahoo DSP (Simulation): http://yahoo.salesagent.local:9580/mcp
       - Yahoo DSP Live (Real API): http://yahoo-live.salesagent.local:9580/mcp
       - NBCU (Linear + Streaming): http://nbcu.salesagent.local:9580/mcp
    
    2. For Yahoo DSP Live, configure real credentials:
       - Update terraform.tfvars with Yahoo DSP API credentials
       - Or use admin UI to configure tenant settings
    
    3. Compare buying experiences:
       - ESPN/CNN/NYT: Direct publisher buys (placement-focused, guaranteed)
       - Yahoo DSP: Programmatic simulation (audience-focused, auction-based)
       - Yahoo DSP Live: REAL Yahoo DSP API integration
       - NBCU: Cross-platform Linear TV + Peacock Streaming
    
    Benefits:
    - ✅ DNS names stay the same across deployments
    - ✅ Automatic IP updates (10s TTL)
    - ✅ No more IP changes breaking Newton!
    - ✅ Direct, programmatic, simulation AND live API in one demo!
    
    Cost: ~$180/month for 6 Fargate tasks (saved $40 by reusing Newton's network!)
    
    Note: Service Discovery DNS only resolves within the VPC
  EOT
}
