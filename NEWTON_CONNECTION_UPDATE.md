# Newton MCP Configuration - Sales Agent Demo

## Task IPs (Updated: 2025-11-23 20:54)

ESPN: 10.118.142.249
CNN: 10.118.137.157
NYT: 10.118.163.92

## Newton DataConnector Configuration

Update `newton/mcp_integration/configs/data_connectors.json`:

```json
{
  "espn_sales": {
    "type": "mcp",
    "deployment_type": "remote",
    "url": "http://10.118.142.249:9580/mcp",
    "transport": "http",
    "description": "ESPN Sports advertising inventory"
  },
  "cnn_sales": {
    "type": "mcp",
    "deployment_type": "remote",
    "url": "http://10.118.137.157:9580/mcp",
    "transport": "http",
    "description": "CNN News advertising inventory"
  },
  "nyt_sales": {
    "type": "mcp",
    "deployment_type": "remote",
    "url": "http://10.118.163.92:9580/mcp",
    "transport": "http",
    "description": "NYT Premium news advertising inventory"
  }
}
```

## What's Fixed

✅ New Docker image deployed with tenant fallback code
✅ MCP server will use `ADCP_TEST_TENANT_ID` environment variable
✅ No authentication required (test mode enabled)
✅ Each ECS service has its own tenant ID:
   - ESPN: `espn`
   - CNN: `cnn`
   - NYT: `nyt`

## Test Commands

```bash
# Test ESPN
curl -X POST http://10.118.142.249:9580/mcp -H "Content-Type: application/json"

# Test CNN
curl -X POST http://10.118.137.157:9580/mcp -H "Content-Type: application/json"

# Test NYT
curl -X POST http://10.118.163.92:9580/mcp -H "Content-Type: application/json"
```

## Expected Result

Newton should now be able to:
1. ✅ Discover tools from all 3 sales agents
2. ✅ Call `get_products` without authentication errors
3. ✅ Each sales agent automatically uses its own tenant context

The "Cannot determine tenant context" error should be **gone**! 🎯

