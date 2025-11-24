output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.salesagent.name
}

output "service_discovery_dns_name" {
  description = "Service Discovery DNS name for this tenant (e.g., espn.salesagent.local)"
  value       = "${var.environment}.salesagent.local"
}

output "service_discovery_namespace_id" {
  description = "Service Discovery namespace ID"
  value       = aws_service_discovery_private_dns_namespace.salesagent.id
}

output "service_discovery_service_arn" {
  description = "Service Discovery service ARN"
  value       = aws_service_discovery_service.tenant.arn
}

