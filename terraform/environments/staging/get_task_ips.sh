#!/bin/bash
# Get Task IPs for Newton MCP Configuration

set -e

REGION="us-east-1"

echo "🔍 Getting task IPs for Newton MCP configuration..."
echo ""

# Function to get task IP (cluster and service have same name)
get_task_ip() {
    local cluster=$1
    local tenant=$2
    
    # List services in the cluster
    SERVICE_ARN=$(aws ecs list-services \
        --cluster "$cluster" \
        --region "$REGION" \
        --query 'serviceArns[0]' \
        --output text 2>/dev/null)
    
    if [ "$SERVICE_ARN" == "None" ] || [ -z "$SERVICE_ARN" ]; then
        echo "⚠️  No services found in cluster $cluster"
        return 1
    fi
    
    # Get service name from ARN
    SERVICE_NAME=$(basename "$SERVICE_ARN")
    
    # Get task ARN
    TASK_ARN=$(aws ecs list-tasks \
        --cluster "$cluster" \
        --service-name "$SERVICE_NAME" \
        --region "$REGION" \
        --query 'taskArns[0]' \
        --output text 2>/dev/null)
    
    if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
        echo "⚠️  No running tasks found for $SERVICE_NAME in cluster $cluster"
        return 1
    fi
    
    TASK_IP=$(aws ecs describe-tasks \
        --cluster "$cluster" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].containers[0].networkInterfaces[0].privateIpv4Address' \
        --output text 2>/dev/null)
    
    if [ -z "$TASK_IP" ] || [ "$TASK_IP" == "None" ]; then
        echo "⚠️  Could not get IP for $SERVICE_NAME"
        return 1
    fi
    
    echo "✅ $tenant: $TASK_IP"
    echo "   Cluster: $cluster"
    echo "   Service: $SERVICE_NAME"
    echo "   MCP URL: http://$TASK_IP:9580/mcp"
    echo ""
}

# Get IPs for each tenant (each has its own cluster)
get_task_ip "salesagent-espn" "ESPN"
get_task_ip "salesagent-cnn" "CNN"
get_task_ip "salesagent-nyt" "NYT"

echo ""
echo "📋 Newton MCP Configuration:"
echo ""
cat <<'EOF'
{
  "espn_sales": {
    "type": "mcp",
    "url": "http://<espn-ip>:9580/mcp",
    "transport": "http",
    "description": "ESPN Sales Agent - Sports advertising inventory"
  },
  "cnn_sales": {
    "type": "mcp",
    "url": "http://<cnn-ip>:9580/mcp",
    "transport": "http",
    "description": "CNN Sales Agent - News advertising inventory"
  },
  "nyt_sales": {
    "type": "mcp",
    "url": "http://<nyt-ip>:9580/mcp",
    "transport": "http",
    "description": "NYT Sales Agent - Premium news advertising inventory"
  }
}
EOF

echo ""
echo "💡 Replace <espn-ip>, <cnn-ip>, <nyt-ip> with the IPs shown above"

