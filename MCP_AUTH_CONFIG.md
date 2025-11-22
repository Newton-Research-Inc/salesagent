# MCP Connection Configuration with Authentication

## 🔐 Authentication Overview

**How it works:**
- Sales agents use **bearer token authentication** via the `x-adcp-auth` header
- Each publisher/tenant has unique auth tokens for their advertisers
- The auth token determines which tenant you're interacting with
- All 3 agents share the same MCP URL, auth token routes to correct tenant

---

## 📋 Newton DataConnector Format

Newton's existing MCP client expects this connection format:

### ESPN Sales Agent (Nike)

```json
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
```

### CNN Sales Agent (Coca-Cola)

```json
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
```

### NYT Sales Agent (Apple)

```json
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

---

## 🔧 How Newton's MCP Client Uses This

Newton's `CustomMCPClient` (in `newton/mcp_integration/mcp_client.py`) will:

1. **Extract the bearer token** from `secrets.bearer_token`
2. **Add it to HTTP headers** as `x-adcp-auth: <token>`
3. **Connect to the MCP server** at the URL
4. **Discover tools** using MCP's `tools/list` protocol
5. **Call tools** with the auth header automatically included

**Example in Newton's code:**
```python
# Newton's MCP client automatically does this:
headers = {
    "x-adcp-auth": connector.secrets["bearer_token"]  # Auto-extracted
}
transport = StreamableHttpTransport(
    url=connector.config["url"],
    headers=headers
)
client = Client(transport=transport)
```

---

## 🧪 Raw FastMCP Client Format

If using `fastmcp` directly (for testing):

```python
from fastmcp.client import Client, StreamableHttpTransport

# ESPN connection
headers = {
    "x-adcp-auth": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA"
}
transport = StreamableHttpTransport(
    url="http://localhost:9580/mcp/",
    headers=headers
)
client = Client(transport=transport)

async with client:
    # List available tools
    tools = await client.list_tools()
    
    # Call a tool
    products = await client.call_tool("get_products", {
        "brief": "Display ads for sports campaign"
    })
```

---

## 🔑 Auth Token Format

**Pattern**: `adcp_{tenant_id}_{random_token}`

**Examples:**
- `adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA`
- `adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM`
- `adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo`

**Components:**
- `adcp_` - Protocol prefix
- `espn` / `cnn` / `nyt` - Tenant ID (publisher)
- `ZgDy...` - 32-character random token (URL-safe base64)

**Security:**
- Each token is tied to a specific principal (advertiser) within a tenant
- Tokens are stored in the `principals` table in PostgreSQL
- No token = no access (authentication required)

---

## 🔄 Switching Between Test Mode and Auth Mode

### Current Setup (Test Mode - No Auth)

**In `.env`:**
```bash
ADCP_TESTING=true
ADCP_TEST_TENANT_ID=espn
ADCP_TEST_PRINCIPAL_ID=nike
```

**What happens:**
- All requests bypass authentication
- Automatically use `tenant=espn`, `principal=nike`
- No token required in headers

### Production Setup (Auth Required)

**In `.env`:**
```bash
# Remove or set to false
ADCP_TESTING=false
# Or simply delete these lines:
# ADCP_TEST_TENANT_ID=
# ADCP_TEST_PRINCIPAL_ID=
```

**What happens:**
- Requests **require** `x-adcp-auth` header
- Token determines tenant + principal
- No token = 401 Unauthorized

---

## 📊 Multi-Tenant Architecture

**Key Design:**
- ✅ **One MCP server** (`http://localhost:9580/mcp/`)
- ✅ **Multiple tenants** in one database (espn, cnn, nyt)
- ✅ **Token-based routing** - auth header determines tenant
- ✅ **Data isolation** - each tenant's data is separate

**Why this design:**
1. **Scalable** - Add 100 publishers without 100 servers
2. **Efficient** - Shared infrastructure, single codebase
3. **Simple** - Newton connects to one URL, changes token per publisher

**Comparison:**

| Approach | URL | Token | Database |
|----------|-----|-------|----------|
| **Our Design** | Same for all (`localhost:9580`) | Different per tenant | Shared (multi-tenant) |
| **Alternative** | Different per tenant (9580, 9581, 9582) | Could be same | Separate per tenant |

We chose the first approach for scalability and simplicity!

---

## 🎯 Production Deployment

When deploying to production (e.g., Fly.io, AWS, GCP):

**Update URLs:**
```json
{
    "name": "ESPN Sales Agent",
    "config": {
        "url": "https://adcp-sales-agent.fly.dev/mcp/",  // ← Production URL
        "deployment_type": "remote"
    },
    "secrets": {
        "bearer_token": "adcp_espn_..."  // ← Same token format
    }
}
```

**Token Management:**
- Store tokens in Newton's secrets manager
- Never commit tokens to git
- Rotate tokens periodically (generate new ones)
- Each advertiser gets their own token

---

## 🧪 Testing Authentication

### Test 1: Verify Token Works

```bash
# With auth (should work)
curl -H "x-adcp-auth: adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA" \
  http://localhost:9580/health

# Without auth (should fail if auth enabled)
curl http://localhost:9580/health
```

### Test 2: Verify Token Routes to Correct Tenant

```python
# ESPN token should see ESPN products
headers_espn = {"x-adcp-auth": "adcp_espn_..."}
espn_products = await client.call_tool("get_products", {})
# Returns ESPN's 3 products

# CNN token should see CNN products
headers_cnn = {"x-adcp-auth": "adcp_cnn_..."}
cnn_products = await client.call_tool("get_products", {})
# Returns CNN's 3 products (different!)
```

### Test 3: Verify Invalid Token Rejected

```python
# Wrong token format
headers = {"x-adcp-auth": "invalid_token"}
# Should return 401 Unauthorized

# Token for wrong tenant
headers = {"x-adcp-auth": "adcp_fake_..."}
# Should return 401 Unauthorized
```

---

## 🔐 Security Best Practices

**For Newton:**
1. ✅ Store tokens in secure secrets manager (not hardcoded)
2. ✅ Use HTTPS in production (not HTTP)
3. ✅ Rotate tokens periodically (every 90 days)
4. ✅ One token per advertiser (don't share)
5. ✅ Log token usage for auditing

**For Sales Agent:**
1. ✅ Validate token format before database lookup
2. ✅ Rate limit per token (prevent abuse)
3. ✅ Log authentication failures
4. ✅ Support token revocation
5. ✅ Use TLS for all connections in production

---

## 📝 Quick Reference

**Newton needs 3 things:**
1. **URL**: `http://localhost:9580/mcp/` (or production URL)
2. **Token**: `adcp_{tenant}_{random}` (from principals table)
3. **Header**: `x-adcp-auth: {token}` (automatically added by MCP client)

**To re-enable auth:**
1. Remove `ADCP_TESTING=true` from `.env`
2. Restart services: `docker-compose restart`
3. Update Newton's DataConnectors with auth tokens
4. Test connection with bearer token

**Status**: Ready for production deployment! 🚀

