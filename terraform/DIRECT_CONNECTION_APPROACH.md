# Direct Connection Approach for Newton Demo

## Architecture Decision

After attempting path-based routing with FastMCP middleware, we've switched to a **simpler, more reliable approach**: Direct VPC connection from Newton to individual tenant ECS tasks.

## Why This Approach?

1. **FastMCP Middleware Limitations**: FastMCP's `add_middleware()` method doesn't reliably apply middleware to its internal Starlette app
2. **VPC-Internal Traffic**: Newton and the sales agent tasks are on the same VPC - direct connection is the intended use case
3. **Lower Latency**: No ALB hop, direct task-to-task communication
4. **Simpler**: Standard MCP protocol with no path rewriting or custom middleware
5. **More Secure**: Traffic stays within VPC, no public ALB needed for MCP

## Implementation

### 3 Separate ECS Services

Instead of one service with path-based routing, we deploy **3 separate ECS services**:

1. **ESPN Sales Agent** (`salesagent-espn`)
   - Environment: `ADCP_TEST_TENANT_ID=espn`, `ADCP_TEST_PRINCIPAL_ID=nike`
   - Port: 9580
   - MCP Endpoint: `http://<task-ip>:9580/mcp`

2. **CNN Sales Agent** (`salesagent-cnn`)
   - Environment: `ADCP_TEST_TENANT_ID=cnn`, `ADCP_TEST_PRINCIPAL_ID=cocacola`
   - Port: 9580
   - MCP Endpoint: `http://<task-ip>:9580/mcp`

3. **NYT Sales Agent** (`salesagent-nyt`)
   - Environment: `ADCP_TEST_TENANT_ID=nyt`, `ADCP_TEST_PRINCIPAL_ID=apple`
   - Port: 9580
   - MCP Endpoint: `http://<task-ip>:9580/mcp`

### Newton Configuration

Newton will configure 3 MCP servers in its data connectors:

```json
{
  "espn_sales": {
    "type": "mcp",
    "url": "http://10.118.131.182:9580/mcp",
    "transport": "http"
  },
  "cnn_sales": {
    "type": "mcp",
    "url": "http://<cnn-task-ip>:9580/mcp",
    "transport": "http"
  },
  "nyt_sales": {
    "type": "mcp",
    "url": "http://<nyt-task-ip>:9580/mcp",
    "transport": "http"
  }
}
```

### Benefits for Newton Demo

1. **Clear Separation**: Each sales agent is a distinct MCP server
2. **Tool Discovery**: Newton discovers tools from each agent independently
3. **Explicit Selection**: When buying ads, Newton explicitly chooses which publisher
4. **Standard Protocol**: No custom path rewriting or header manipulation

## Next Steps

1. ✅ Remove ALB path-based routing configuration (not needed)
2. ✅ Remove PathPrefixMiddleware from `main.py` (not needed)
3. 🔄 Create Terraform module for tenant-specific ECS services
4. 🔄 Deploy 3 services with correct environment variables
5. 🔄 Provide Newton with task IPs for connection

## Cost Impact

- **Same cost**: 3 tasks running vs 1 task with complex routing
- **No ALB cost for MCP**: MCP traffic doesn't use ALB (VPC-internal only)
- **ALB still used**: Admin UI and A2A services still accessible via ALB if needed

## Migration from Path-Based Routing

We're keeping the existing `salesagent-staging` service as the ESPN agent and adding 2 more services for CNN and NYT. This allows us to test the direct connection approach without disrupting the existing deployment.

