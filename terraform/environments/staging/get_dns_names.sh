#!/bin/bash
set -e

echo "🔍 Service Discovery DNS Names for Sales Agents"
echo "================================================"
echo ""
echo "Newton MCP Server Configuration:"
echo ""
echo "ESPN Sales Agent:"
echo "  URL: http://espn.salesagent.local:9580/mcp"
echo "  Admin: http://espn.salesagent.local:9501"
echo "  A2A: http://espn.salesagent.local:9591"
echo ""
echo "CNN Sales Agent:"
echo "  URL: http://cnn.salesagent.local:9580/mcp"
echo "  Admin: http://cnn.salesagent.local:9501"
echo "  A2A: http://cnn.salesagent.local:9591"
echo ""
echo "NYT Sales Agent:"
echo "  URL: http://nyt.salesagent.local:9580/mcp"
echo "  Admin: http://nyt.salesagent.local:9501"
echo "  A2A: http://nyt.salesagent.local:9591"
echo ""
echo "✅ These DNS names are stable and will NOT change across deployments!"
echo ""
echo "Newton DataConnector Configuration:"
echo "------------------------------------"
cat <<'EOF'
{
  "mcp_servers": {
    "espn_sales_agent": {
      "command": "python",
      "args": ["-m", "fastmcp.mcp_integration.mcp_client"],
      "env": {
        "MCP_SERVER_URL": "http://espn.salesagent.local:9580/mcp",
        "DEPLOYMENT_TYPE": "remote"
      }
    },
    "cnn_sales_agent": {
      "command": "python",
      "args": ["-m", "fastmcp.mcp_integration.mcp_client"],
      "env": {
        "MCP_SERVER_URL": "http://cnn.salesagent.local:9580/mcp",
        "DEPLOYMENT_TYPE": "remote"
      }
    },
    "nyt_sales_agent": {
      "command": "python",
      "args": ["-m", "fastmcp.mcp_integration.mcp_client"],
      "env": {
        "MCP_SERVER_URL": "http://nyt.salesagent.local:9580/mcp",
        "DEPLOYMENT_TYPE": "remote"
      }
    }
  }
}
EOF

