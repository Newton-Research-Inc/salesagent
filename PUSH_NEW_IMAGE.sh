#!/bin/bash
# Push new Docker image with tenant fallback code to ECR

set -e

echo "=== Step 1: Login to ECR ==="
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 381492092437.dkr.ecr.us-east-1.amazonaws.com

echo ""
echo "=== Step 2: Push new image ==="
docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

echo ""
echo "=== Step 3: Verify new image in ECR ==="
aws ecr describe-images \
  --repository-name salesagent-staging \
  --region us-east-1 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-1].{Pushed:imagePushedAt,Tags:imageTags,Digest:imageDigest}' \
  --output table

echo ""
echo "=== Step 4: Force ECS to pull new image ==="
for CLUSTER in salesagent-espn salesagent-cnn salesagent-nyt; do
  echo "Deploying to $CLUSTER..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$CLUSTER" \
    --force-new-deployment \
    --region us-east-1 \
    --no-cli-pager
done

echo ""
echo "✅ Deployment initiated - services will pull new image"
echo "⏱️  Wait 2-3 minutes for new tasks to start"
echo ""
echo "Then run: bash terraform/environments/staging/get_task_ips.sh"

