#!/bin/bash
# Test if MCP endpoints are responding

echo "=== Testing MCP Endpoint Responses ==="

echo ""
echo "📡 ESPN (10.118.142.249:9580):"
timeout 5 curl -v -X POST http://10.118.142.249:9580/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}' 2>&1 | head -20

echo ""
echo "📡 CNN (10.118.137.157:9580):"
timeout 5 curl -v -X POST http://10.118.137.157:9580/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"ping","id":1}' 2>&1 | head -20

echo ""
echo "💡 Look for:"
echo "   - 'Connected' or '200 OK' = MCP server is responding"
echo "   - 'Connection refused' = MCP server not running"
echo "   - Timeout = MCP server hanging"

