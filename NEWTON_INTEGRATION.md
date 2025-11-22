# Newton Integration Guide - AdCP Sales Agents

## 🎉 Setup Complete!

Three AdCP Sales Agent servers are now running with unique publishers and advertisers configured for Newton integration.

## Services Status

All services running on **non-conflicting ports** (95xx range):

- **PostgreSQL**: `localhost:9532`
- **MCP Server**: `localhost:9580` 
- **A2A Server**: `localhost:9591`
- **Admin UI**: `localhost:9501`

Health check:
```bash
curl http://localhost:9580/health
curl http://localhost:9501/health
```

## Sales Agents Configuration

### 1. ESPN Sales Agent
- **Publisher**: ESPN
- **Advertiser**: Nike Inc.
- **Principal ID**: `nike`
- **Tenant ID**: `espn`
- **MCP URL**: `http://localhost:9580/mcp/`
- **Auth Header**: `x-adcp-auth: adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA`

### 2. CNN Sales Agent
- **Publisher**: CNN
- **Advertiser**: Coca-Cola
- **Principal ID**: `cocacola`
- **Tenant ID**: `cnn`
- **MCP URL**: `http://localhost:9580/mcp/`
- **Auth Header**: `x-adcp-auth: adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM`

### 3. New York Times Sales Agent
- **Publisher**: New York Times (NYT)
- **Advertiser**: Apple Inc.
- **Principal ID**: `apple`
- **Tenant ID**: `nyt`
- **MCP URL**: `http://localhost:9580/mcp/`
- **Auth Header**: `x-adcp-auth: adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo`

## Newton Integration Steps

### Option 1: MCP Client Integration (Recommended for Auto-Discovery)

Newton's existing MCP client (`newton/mcp_integration/mcp_client.py`) can connect directly to each sales agent:

```python
# In Newton's DataConnector model, create 3 MCP server connections:

# ESPN Sales Agent
{
    "name": "ESPN Sales Agent",
    "connector_type": "MCP_SERVER",
    "config": {
        "url": "http://localhost:9580/mcp/",
        "deployment_type": "remote"
    },
    "secrets": {
        "bearer_token": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"
    }
}

# CNN Sales Agent  
{
    "name": "CNN Sales Agent",
    "connector_type": "MCP_SERVER",
    "config": {
        "url": "http://localhost:9580/mcp/",
        "deployment_type": "remote"
    },
    "secrets": {
        "bearer_token": "adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM"
    }
}

# NYT Sales Agent
{
    "name": "NYT Sales Agent",
    "connector_type": "MCP_SERVER",
    "config": {
        "url": "http://localhost:9580/mcp/",
        "deployment_type": "remote"
    },
    "secrets": {
        "bearer_token": "adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo"
    }
}
```

**Key Point**: All three sales agents share the **same MCP URL** (`http://localhost:9580/mcp/`), but use **different auth tokens**. The token determines which tenant (publisher) you're buying from.

### Option 2: Python Client with `adcp` Library

Install the official AdCP client library:

```bash
pip install adcp
```

Example usage:

```python
from adcp import ADCPMultiAgentClient

# Initialize multi-agent client
client = ADCPMultiAgentClient([
    {
        "name": "ESPN",
        "mcp_url": "http://localhost:9580/mcp/",
        "auth_token": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"
    },
    {
        "name": "CNN",
        "mcp_url": "http://localhost:9580/mcp/",
        "auth_token": "adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM"
    },
    {
        "name": "NYT",
        "mcp_url": "http://localhost:9580/mcp/",
        "auth_token": "adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo"
    }
])

# Get products from all agents
products = await client.get_products(brief="Display ads for Nike campaign")

# Create media buy with ESPN
media_buy = await client.create_media_buy(
    agent_name="ESPN",
    promoted_offering="Nike Air Jordan",
    buyer_ref="newton_campaign_001",
    packages=[...],
    # ... other params
)
```

## Available AdCP Tools

Each sales agent exposes these MCP tools:

1. **`get_products`** - Query available advertising products
2. **`create_media_buy`** - Create a new advertising campaign
3. **`update_media_buy`** - Modify an existing campaign
4. **`get_media_buy_delivery`** - Check campaign performance
5. **`sync_creatives`** - Upload creative assets
6. **`list_creatives`** - List uploaded creatives
7. **`get_signals`** - Get audience signals for targeting
8. **`list_creative_formats`** - List supported creative formats
9. **`list_authorized_properties`** - List available inventory
10. **`update_performance_index`** - Update campaign optimization

## Testing the Integration

### Test 1: List Available Tools

```python
from fastmcp.client import Client, StreamableHttpTransport

# Connect to ESPN
headers = {"x-adcp-auth": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"}
transport = StreamableHttpTransport(url="http://localhost:9580/mcp/", headers=headers)
client = Client(transport=transport)

async with client:
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
    
    # Get products
    products = await client.call_tool("get_products", {"brief": "video ads"})
    print(f"Found {len(products)} products")
```

### Test 2: Create a Media Buy

```python
# Create a simple media buy on ESPN
result = await client.call_tool("create_media_buy", {
    "promoted_offering": "Nike Air Jordan",
    "buyer_ref": "newton_test_001",
    "packages": [
        {
            "package_ref": "pkg_001",
            "product_ref": "display_300x250",  # Standard display ad
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "pricing": {
                "pricing_model": "CPM",
                "rate": 5.00,
                "currency": "USD"
            },
            "inventory_requests": [
                {
                    "quantity": 100000,  # 100k impressions
                    "unit": "IMPRESSIONS"
                }
            ]
        }
    ]
})
```

## Managing Sales Agents

### Start/Stop Services

```bash
# Start all services
cd /Users/danfinkel/github/opensource/salesagent
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f adcp-server

# Stop services
docker-compose down
```

### Access Admin UI

Visit `http://localhost:9501` to manage tenants, principals, and view campaign activity.

**Login**: Use the admin emails configured for each tenant:
- ESPN: `admin@espn.com`
- CNN: `admin@cnn.com`
- NYT: `admin@nytimes.com`

(Note: For local development, you may need to configure Google OAuth or use test mode)

### Add More Publishers

```bash
# Inside container
docker-compose exec adcp-server sh -c "cd /app && PYTHONPATH=/app python scripts/setup/setup_tenant.py 'Publisher Name' --adapter mock --admin-email admin@publisher.com"

# Then create a principal (advertiser) for that publisher
docker-compose exec adcp-server python -c "
import secrets
from sqlalchemy import select
from src.core.database.database_session import get_db_session
from src.core.database.models import Principal

tenant_id = 'your_tenant_id'
principal_id = 'your_advertiser'
name = 'Advertiser Name'
token = f'adcp_{tenant_id}_{secrets.token_urlsafe(32)}'

with get_db_session() as session:
    principal = Principal(
        tenant_id=tenant_id,
        principal_id=principal_id,
        name=name,
        platform_mappings={'mock': {'advertiser_id': principal_id}},
        access_token=token
    )
    session.add(principal)
    session.commit()
    print(f'Token: {token}')
"
```

## Architecture Notes

### Multi-Tenancy Design

The AdCP Sales Agent uses a **single MCP server** that supports **multi-tenant authentication**:

- ✅ **One MCP server instance** running on port 9580
- ✅ **Multiple tenants** (ESPN, CNN, NYT) in one database
- ✅ **Token-based routing** - The `x-adcp-auth` header determines which tenant you're interacting with
- ✅ **Isolated data** - Each tenant's campaigns, creatives, and settings are completely separate

This is different from running separate MCP server instances per publisher. Benefits:

1. **Scalable**: Add 100 publishers without spinning up 100 servers
2. **Efficient**: Single codebase, shared infrastructure
3. **Simple**: Newton connects to one URL, just changes the auth token

### Newton's Tool Aggregation Strategy

To avoid "tool explosion" (3 agents × 10 tools = 30 tools), Newton should use **agent abstraction**:

```python
# Instead of: espn_get_products(), cnn_get_products(), nyt_get_products()
# Use one tool with agent parameter:

def get_products(agent_name: str, brief: str, **kwargs):
    """
    Get advertising products from a sales agent.
    
    Args:
        agent_name: Which sales agent to query ("ESPN", "CNN", "NYT")
        brief: Description of what you're looking for
    """
    # Route to the appropriate agent based on agent_name
    token = AGENT_TOKENS[agent_name]
    return adcp_client.get_products(token=token, brief=brief, **kwargs)
```

This keeps Newton's tool count constant regardless of how many sales agents you add.

## Next Steps

1. **Configure Newton's MCP Client**: Add the three sales agents as DataConnectors
2. **Test Connection**: Use Newton's `MCPToolBridge` to discover tools from each agent
3. **Implement Tool Aggregation**: Create a wrapper layer that presents unified tools with `agent_name` parameter
4. **Test Media Buys**: Have Newton create test campaigns on each platform
5. **Monitor Results**: Use Admin UI to view campaign status and delivery

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs adcp-server
docker-compose logs admin-ui

# Common issue: Missing .env.secrets file
# Make sure .env.secrets is merged into .env
```

### Authentication failures
- Verify the auth token matches exactly (no extra spaces)
- Check that the principal exists: Access Admin UI → Select tenant → Principals tab
- Tokens are case-sensitive

### Port conflicts
- Check if ports are already in use: `lsof -i :9580`
- Modify `.env` file to use different ports if needed

### Can't connect to MCP server
- MCP uses Server-Sent Events (SSE), requires proper client library
- Use `fastmcp.Client` with `StreamableHttpTransport`
- Don't use plain `curl` for testing (won't work with SSE)

## Resources

- **AdCP Specification**: https://adcontextprotocol.org/
- **FastMCP Docs**: https://github.com/jlowin/fastmcp
- **Sales Agent Repo**: /Users/danfinkel/github/opensource/salesagent
- **Newton Repo**: /Users/danfinkel/github/newton/nri-server/

---

**Status**: ✅ Ready for Newton integration!
**Created**: November 18, 2025

