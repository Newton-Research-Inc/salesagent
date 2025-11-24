#!/bin/bash
# Check if tasks are using the new Docker image

echo "=== Checking task image digests ==="
echo "Expected new digest: sha256:352de7953a6157f024e114c5bfa4834e550c80ddac1d722cea45f85ca41164a4"
echo ""

for CLUSTER in salesagent-espn salesagent-cnn salesagent-nyt; do
  echo "📊 $CLUSTER:"
  
  TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER" --region us-east-1 --query 'taskArns[0]' --output text)
  
  if [[ "$TASK_ARN" != "None" && "$TASK_ARN" != "" ]]; then
    aws ecs describe-tasks \
      --cluster "$CLUSTER" \
      --tasks "$TASK_ARN" \
      --region us-east-1 \
      --query 'tasks[0].{LastStatus:lastStatus,ImageDigest:containers[0].imageDigest,StartedAt:startedAt,IP:containers[0].networkInterfaces[0].privateIpv4Address}' \
      --output table
  else
    echo "❌ No tasks running"
  fi
  echo ""
done

echo "💡 If ImageDigest matches 352de7953a..., the new image is deployed!"
echo "💡 If ImageDigest is 98020d353f..., ECS is still using the old image"

