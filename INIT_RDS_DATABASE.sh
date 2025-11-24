#!/bin/bash
# Initialize RDS database with demo tenants, products, and data

echo "=== Initializing RDS Database ==="
echo ""
echo "We'll use the ESPN container to run database initialization"
echo ""

# Get ESPN task ID
TASK_ARN=$(aws ecs list-tasks --cluster salesagent-espn --region us-east-1 --query 'taskArns[0]' --output text)
TASK_ID=$(echo "$TASK_ARN" | awk -F'/' '{print $NF}')

echo "📦 ESPN Task ID: $TASK_ID"
echo ""

echo "=== Step 1: Run Alembic migrations ==="
aws ecs execute-command \
  --cluster salesagent-espn \
  --task "$TASK_ID" \
  --container salesagent-espn \
  --region us-east-1 \
  --interactive \
  --command "cd /app && python migrate.py"

echo ""
echo "=== Step 2: Initialize demo data ==="
echo "Creating demo script in container..."

# Create init script that will run inside the container
aws ecs execute-command \
  --cluster salesagent-espn \
  --task "$TASK_ID" \
  --container salesagent-espn \
  --region us-east-1 \
  --interactive \
  --command "cd /app && python -c '
import os
os.environ[\"PYTHONPATH\"] = \"/app\"

from scripts.setup.create_test_tenants import create_demo_tenants_and_products

# Create demo tenants with products
print(\"Creating demo tenants: ESPN, CNN, NYT\")
create_demo_tenants_and_products()

print(\"✅ Database initialized successfully!\")
'"

echo ""
echo "✅ Database initialization complete!"
echo ""
echo "Now test again with Newton - tenants should be found"

