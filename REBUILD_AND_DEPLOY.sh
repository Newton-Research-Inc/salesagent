#!/bin/bash
# Rebuild and deploy with tenant initialization

set -e

echo "=== Step 1: Rebuild Docker image ==="
docker build --platform linux/amd64 --no-cache -t salesagent:latest . 2>&1 | tail -20

echo ""
echo "=== Step 2: Tag and push to ECR ==="
docker tag salesagent:latest 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 381492092437.dkr.ecr.us-east-1.amazonaws.com

docker push 381492092437.dkr.ecr.us-east-1.amazonaws.com/salesagent-staging:latest

echo ""
echo "=== Step 3: Force ECS to pull new image ==="
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
echo "✅ Deployment complete!"
echo "⏱️  Wait 2-3 minutes for containers to start and initialize database"
echo ""
echo "Then check logs:"
echo "   aws logs tail /ecs/salesagent-espn --region us-east-1 --since 5m | grep -E '(Creating tenant|✅ Created tenant|Demo tenants)'"

