#!/bin/bash
# Get Task IPs for Newton MCP Configuration

set -e

REGION="us-east-1"
CLUSTER="salesagent-staging"

echo "🔍 Getting task IPs for Newton MCP configuration..."
echo ""

# Function to get task IP
get_task_ip() {
    local service=$1
    local tenant=$2
    
    TASK_ARN=$(aws ecs list-tasks \
        --cluster "$CLUSTER" \
        --service-name "$service" \
        --region "$REGION" \
        --query 'taskArns[0]' \
        --output text 2>/dev/null)
    
    if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
        echo "⚠️  No running tasks found for $service"
        return 1
    fi
    
    TASK_IP=$(aws ecs describe-tasks \
        --cluster "$CLUSTER" \
        --tasks "$TASK_ARN" \
        --region "$REGION" \
        --query 'tasks[0].containers[0].networkInterfaces[0].privateIpv4Address' \
        --output text 2>/dev/null)
    
    if [ -z "$TASK_IP" ] || [ "$TASK_IP" == "None" ]; then
        echo "⚠️  Could not get IP for $service"
        return 1
    fi
    
    echo "✅ $tenant: $TASK_IP"
    echo "   MCP URL: http://$TASK_IP:9580/mcp"
    echo ""
}

# Get IPs for each tenant
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

