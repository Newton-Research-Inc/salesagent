variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "service_discovery_namespace_id" {
  description = "Service Discovery namespace ID (shared across all tenants)"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "mcp_target_group_arn" {
  description = "ARN of MCP target group"
  type        = string
}

variable "admin_target_group_arn" {
  description = "ARN of Admin target group"
  type        = string
}

variable "a2a_target_group_arn" {
  description = "ARN of A2A target group"
  type        = string
}

variable "db_host" {
  description = "Database host"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "gemini_api_key" {
  description = "Gemini API key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "super_admin_emails" {
  description = "Super admin emails"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL for Docker image"
  type        = string
}

variable "tenant_id" {
  description = "Tenant ID for this service (espn, cnn, nyt)"
  type        = string
  default     = "espn"
}

variable "principal_id" {
  description = "Default principal ID for testing (nike, cocacola, apple)"
  type        = string
  default     = "nike"
}

# Yahoo DSP Live API Credentials (optional - only needed for yahoo_live tenant)
variable "yahoo_dsp_client_id" {
  description = "Yahoo DSP OAuth Client ID (Secrets Manager ARN)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "yahoo_dsp_client_secret" {
  description = "Yahoo DSP OAuth Client Secret (Secrets Manager ARN)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "yahoo_dsp_seat_id" {
  description = "Yahoo DSP Seat ID"
  type        = string
  default     = ""
}

variable "yahoo_dsp_advertiser_id" {
  description = "Yahoo DSP Advertiser ID"
  type        = string
  default     = ""
}

variable "yahoo_dsp_test_mode" {
  description = "Yahoo DSP Test Mode - when 'true', creates INACTIVE campaigns with max $5 budget. Set to 'false' for production."
  type        = string
  default     = "true"  # Default to test mode for safety
}

variable "enabled_tools" {
  description = "Comma-separated list of enabled tools. Use 'all' for all tools (default), 'core' for core AdCP tools only, 'core,yahoo' for core + Yahoo tools, etc."
  type        = string
  default     = "all"  # Default to all tools (backward compatible)
}
