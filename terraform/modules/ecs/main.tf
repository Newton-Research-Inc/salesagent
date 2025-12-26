# ============================================================================
# Service Discovery (AWS Cloud Map)
# ============================================================================
# Service Discovery service for this tenant (espn, cnn, or nyt)
# Registers ECS tasks automatically and maintains A records in the shared namespace
resource "aws_service_discovery_service" "tenant" {
  name = var.environment  # e.g., "espn" creates espn.salesagent.local

  dns_config {
    namespace_id = var.service_discovery_namespace_id

    dns_records {
      ttl  = 10  # Low TTL for quick updates when tasks change
      type = "A"
    }

    routing_policy = "MULTIVALUE"  # Return all healthy task IPs
  }

  health_check_custom_config {
    failure_threshold = 1  # Mark unhealthy after 1 failed check
  }

  tags = {
    Name        = "salesagent-${var.environment}-discovery"
    Environment = var.environment
  }
}

# ============================================================================
# ECS Cluster
# ============================================================================
resource "aws_ecs_cluster" "main" {
  name = "salesagent-${var.environment}"

  tags = {
    Name        = "salesagent-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/salesagent-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "salesagent-${var.environment}-logs"
    Environment = var.environment
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name = "salesagent-${var.environment}-ecs-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "salesagent-${var.environment}-ecs-task-execution"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "salesagent-${var.environment}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "salesagent-${var.environment}-ecs-task"
    Environment = var.environment
  }
}

resource "aws_ecs_task_definition" "salesagent" {
  family                   = "salesagent-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "salesagent-${var.environment}"
      image     = "${var.ecr_repository_url}:latest"
      essential = true

      environment = concat([
        { name = "DATABASE_URL", value = "postgresql://${var.db_username}:${var.db_password}@${var.db_host}:5432/${var.db_name}" },
        { name = "ENVIRONMENT", value = "production" },
        { name = "ADCP_TESTING", value = "true" },
        { name = "ADCP_DEMO_MODE", value = "true" },
        { name = "ADCP_TEST_TENANT_ID", value = var.tenant_id },
        { name = "ADCP_TEST_PRINCIPAL_ID", value = var.principal_id },
        { name = "ADCP_PORT", value = "9580" },
        { name = "ADCP_HOST", value = "0.0.0.0" },
        { name = "ADMIN_UI_PORT", value = "9501" },
        { name = "A2A_PORT", value = "9591" },
        { name = "SUPER_ADMIN_EMAILS", value = var.super_admin_emails },
        # Tool filtering - controls which MCP tools are exposed
        # Use "all" for all tools (default), "core" for core AdCP only, "core,yahoo" for core + Yahoo, etc.
        { name = "ENABLED_TOOLS", value = var.enabled_tools }
      ],
      # Yahoo DSP Live credentials (only included if seat_id is provided)
      var.yahoo_dsp_seat_id != "" ? [
        { name = "YAHOO_DSP_SEAT_ID", value = var.yahoo_dsp_seat_id },
        { name = "YAHOO_DSP_ADVERTISER_ID", value = var.yahoo_dsp_advertiser_id },
        # TEST MODE ENABLED BY DEFAULT - Creates INACTIVE campaigns with max $5 budget
        # Set to "false" in production when ready to go live
        { name = "YAHOO_DSP_TEST_MODE", value = var.yahoo_dsp_test_mode }
      ] : [])

      secrets = concat([
        { name = "GEMINI_API_KEY", valueFrom = var.gemini_api_key },
        { name = "GOOGLE_CLIENT_ID", valueFrom = var.google_client_id },
        { name = "GOOGLE_CLIENT_SECRET", valueFrom = var.google_client_secret }
      ],
      # Yahoo DSP Live secrets (only included if client_id is provided)
      var.yahoo_dsp_client_id != "" ? [
        { name = "YAHOO_DSP_CLIENT_ID", valueFrom = var.yahoo_dsp_client_id },
        { name = "YAHOO_DSP_CLIENT_SECRET", valueFrom = var.yahoo_dsp_client_secret }
      ] : [])

      portMappings = [
        {
          containerPort = 9580
          protocol      = "tcp"
        },
        {
          containerPort = 9501
          protocol      = "tcp"
        },
        {
          containerPort = 9591
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name        = "salesagent-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_ecs_service" "salesagent" {
  name            = "salesagent-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.salesagent.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = false
  }

  # Service Discovery registration
  # Automatically registers task IPs to DNS (e.g., espn.salesagent.local)
  service_registries {
    registry_arn = aws_service_discovery_service.tenant.arn
  }

  # Load balancer blocks removed - using Service Discovery DNS names for Newton
  # Service Discovery provides stable DNS names that automatically update when tasks change IPs
  # This is more reliable than ALB for VPC-internal MCP clients

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution
  ]

  tags = {
    Name        = "salesagent-${var.environment}"
    Environment = var.environment
  }
}

