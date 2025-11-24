#!/bin/bash
# Check ECS deployment status after pushing new image

echo "=== Checking ECS service status ==="
for CLUSTER in salesagent-espn salesagent-cnn salesagent-nyt; do
  echo ""
  echo "📊 Cluster: $CLUSTER"
  aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$CLUSTER" \
    --region us-east-1 \
    --query 'services[0].{Status:status,Running:runningCount,Pending:pendingCount,Desired:desiredCount}' \
    --output table
  
  echo "Latest deployment:"
  aws ecs describe-services \
    --cluster "$CLUSTER" \
    --services "$CLUSTER" \
    --region us-east-1 \
    --query 'services[0].deployments[0].{Status:status,Running:runningCount,Pending:pendingCount,TaskDef:taskDefinition}' \
    --output table
done

echo ""
echo "💡 When all services show Running: 1, get the new task IPs:"
echo "   bash terraform/environments/staging/get_task_ips.sh"

