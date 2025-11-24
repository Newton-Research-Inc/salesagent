#!/bin/bash
# Initialize RDS database using ECS Exec

echo "=== Initializing RDS Database via ECS Exec ==="

# Use ESPN container
CLUSTER="salesagent-espn"
SERVICE="salesagent-espn"

echo "Getting task ID for $CLUSTER..."
TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER" --region us-east-1 --query 'taskArns[0]' --output text)

if [[ "$TASK_ARN" == "None" || -z "$TASK_ARN" ]]; then
  echo "❌ No running tasks found in cluster $CLUSTER"
  exit 1
fi

TASK_ID=$(echo "$TASK_ARN" | awk -F'/' '{print $NF}')
echo "✅ Task ID: $TASK_ID"
echo ""

echo "📝 Running database initialization script in container..."
echo "   This will create ESPN, CNN, and NYT tenants with products"
echo ""

# Run the init script
aws ecs execute-command \
  --cluster "$CLUSTER" \
  --task "$TASK_ID" \
  --container "$CLUSTER" \
  --region us-east-1 \
  --command "/bin/bash -c 'cd /app && python scripts/setup/init_database.py'" \
  --interactive

echo ""
echo "💡 If you see 'The execute command failed', ECS Exec may not be enabled."
echo "   Alternative: We'll need to add init code to the Docker entrypoint"

