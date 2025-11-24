#!/bin/bash
# Check CloudWatch logs for MCP server startup

echo "=== Checking ESPN MCP Server Logs (last 50 lines) ==="
aws logs tail /ecs/salesagent-espn --region us-east-1 --since 5m --format short | grep -E "(MCP|Error|Exception|Traceback)" | tail -50

echo ""
echo "=== Checking CNN MCP Server Logs (last 50 lines) ==="
aws logs tail /ecs/salesagent-cnn --region us-east-1 --since 5m --format short | grep -E "(MCP|Error|Exception|Traceback)" | tail -50

echo ""
echo "=== Checking NYT MCP Server Logs (last 50 lines) ==="
aws logs tail /ecs/salesagent-nyt --region us-east-1 --since 5m --format short | grep -E "(MCP|Error|Exception|Traceback)" | tail -50

echo ""
echo "💡 Look for:"
echo "   - 'Starting MCP server on port 9580' (should appear)"
echo "   - Any Python errors or exceptions"
echo "   - 'Cannot determine tenant context' messages"

