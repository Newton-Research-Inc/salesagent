output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the load balancer"
  value       = aws_lb.main.zone_id
}

output "alb_arn" {
  description = "ARN of the load balancer"
  value       = aws_lb.main.arn
}

output "mcp_target_group_arn" {
  description = "ARN of MCP target group"
  value       = aws_lb_target_group.mcp.arn
}

output "admin_target_group_arn" {
  description = "ARN of Admin target group"
  value       = aws_lb_target_group.admin.arn
}

output "a2a_target_group_arn" {
  description = "ARN of A2A target group"
  value       = aws_lb_target_group.a2a.arn
}

