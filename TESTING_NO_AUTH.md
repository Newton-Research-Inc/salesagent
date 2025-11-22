# Testing Configuration - No Authentication Required

## 🎉 Setup Complete!

Three separate sales agent instances are now running, each with:
- ✅ **No authentication required**
- ✅ **Unique URLs (different ports)**
- ✅ **Pre-configured tenant and principal**

---

## Sales Agent URLs

### ESPN Sales Agent
- **URL**: `http://localhost:9580/mcp/`
- **Port**: 9580
- **Tenant**: ESPN
- **Principal**: Nike Inc.
- **No auth needed** - Automatically uses ESPN tenant

### CNN Sales Agent
- **URL**: `http://localhost:9581/mcp/`
- **Port**: 9581
- **Tenant**: CNN
- **Principal**: Coca-Cola
- **No auth needed** - Automatically uses CNN tenant

### NYT Sales Agent
- **URL**: `http://localhost:9582/mcp/`
- **Port**: 9582
- **Tenant**: New York Times
- **Principal**: Apple Inc.
- **No auth needed** - Automatically uses NYT tenant

---

## Newton Configuration

In Newton's DataConnector settings, add three MCP servers:

### ESPN
```json
{
  "name": "ESPN Sales Agent",
  "url": "http://localhost:9580/mcp/",
  "auth_type": "None"  // No authentication required!
}
```

### CNN
```json
{
  "name": "CNN Sales Agent",
  "url": "http://localhost:9581/mcp/",
  "auth_type": "None"  // No authentication required!
}
```

### NYT
```json
{
  "name": "NYT Sales Agent",
  "url": "http://localhost:9582/mcp/",
  "auth_type": "None"  // No authentication required!
}
```

---

## Quick Test

Test that each endpoint works without authentication:

```bash
# ESPN - Get products
curl -X POST http://localhost:9580/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_products",
      "arguments": {"brief": "sports inventory"}
    },
    "id": 1
  }'

# CNN - Get products
curl -X POST http://localhost:9581/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_products",
      "arguments": {"brief": "news inventory"}
    },
    "id": 1
  }'

# NYT - Get products
curl -X POST http://localhost:9582/mcp/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_products",
      "arguments": {"brief": "premium inventory"}
    },
    "id": 1
  }'
```

---

## Managing Services

### Start Services
```bash
cd /Users/danfinkel/github/opensource/salesagent
docker-compose -f docker-compose.testing.yml up -d
```

### Check Status
```bash
docker-compose -f docker-compose.testing.yml ps
```

Expected output:
```
NAME                      STATUS                  PORTS
salesagent-cnn-agent-1    Up (healthy)           0.0.0.0:9581->8080/tcp
salesagent-espn-agent-1   Up (healthy)           0.0.0.0:9580->8080/tcp
salesagent-nyt-agent-1    Up (healthy)           0.0.0.0:9582->8080/tcp
salesagent-postgres-1     Up (healthy)           0.0.0.0:9532->5432/tcp
```

### View Logs
```bash
# ESPN logs
docker-compose -f docker-compose.testing.yml logs -f espn-agent

# CNN logs
docker-compose -f docker-compose.testing.yml logs -f cnn-agent

# NYT logs
docker-compose -f docker-compose.testing.yml logs -f nyt-agent
```

### Stop Services
```bash
docker-compose -f docker-compose.testing.yml down
```

---

## Test Mode Indicators

When services start, you'll see test mode indicators in the logs:

```
🧪 TEST MODE: tenant=espn, principal=nike
🧪 TEST MODE: tenant=cnn, principal=cocacola
🧪 TEST MODE: tenant=nyt, principal=apple
```

---

## Example: Python Testing

```python
from fastmcp.client import Client
from fastmcp.transports import StreamableHttpTransport

# ESPN - No auth header needed!
transport = StreamableHttpTransport(url="http://localhost:9580/mcp/")
client = Client(transport=transport)

async with client:
    # Get products
    products = await client.call_tool("get_products", {
        "brief": "Display inventory for basketball campaign"
    })
    print(f"ESPN Products: {len(products['products'])}")
    
    # Create media buy
    media_buy = await client.call_tool("create_media_buy", {
        "promoted_offering": "Nike Air Jordan",
        "buyer_ref": "test_001",
        "packages": [{
            "package_ref": "pkg_001",
            "product_ref": "espn_homepage_leaderboard",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "pricing": {
                "pricing_model": "CPM",
                "rate": 12.00,
                "currency": "USD"
            },
            "inventory_requests": [{
                "quantity": 1000000,
                "unit": "IMPRESSIONS"
            }]
        }]
    })
    print(f"Media Buy Created: {media_buy['media_buy_id']}")
```

---

## How It Works

### Test Mode Configuration

Each sales agent instance runs with these environment variables:

**ESPN Agent:**
```bash
ADCP_TESTING=true
ADCP_TEST_TENANT_ID=espn
ADCP_TEST_PRINCIPAL_ID=nike
```

**CNN Agent:**
```bash
ADCP_TESTING=true
ADCP_TEST_TENANT_ID=cnn
ADCP_TEST_PRINCIPAL_ID=cocacola
```

**NYT Agent:**
```bash
ADCP_TESTING=true
ADCP_TEST_TENANT_ID=nyt
ADCP_TEST_PRINCIPAL_ID=apple
```

### Authentication Bypass

When `ADCP_TESTING=true`, the authentication code (`src/core/auth.py`) automatically:
1. Bypasses token validation
2. Uses the configured test tenant
3. Uses the configured test principal
4. Logs a test mode indicator

This happens in `get_principal_from_context()`:
```python
if os.getenv("ADCP_TESTING") == "true":
    test_tenant_id = os.getenv("ADCP_TEST_TENANT_ID")
    test_principal_id = os.getenv("ADCP_TEST_PRINCIPAL_ID")
    return (test_principal_id, {"tenant_id": test_tenant_id})
```

---

## Benefits

✅ **Simpler Testing** - No auth tokens to manage  
✅ **Clear URLs** - Each tenant has unique port  
✅ **Isolated Services** - Each runs independently  
✅ **Easy Newton Config** - Just 3 URLs, no auth  
✅ **Same Data** - All share the same PostgreSQL database

---

## Switching Back to Production Mode

To switch back to the production configuration with authentication:

```bash
# Stop testing services
docker-compose -f docker-compose.testing.yml down

# Start production services (with auth)
docker-compose up -d
```

Production mode requires authentication tokens:
- ESPN: `adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA`
- CNN: `adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM`
- NYT: `adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo`

---

## Troubleshooting

### Port Already in Use
If ports 9580, 9581, or 9582 are in use:

```bash
# Check what's using the ports
lsof -i :9580
lsof -i :9581
lsof -i :9582

# Kill the processes or modify docker-compose.testing.yml ports
```

### Service Won't Start
```bash
# Check logs for errors
docker-compose -f docker-compose.testing.yml logs espn-agent

# Rebuild containers
docker-compose -f docker-compose.testing.yml up -d --build
```

### Database Issues
```bash
# Reset database (WARNING: Deletes all data)
docker-compose -f docker-compose.testing.yml down -v
docker-compose -f docker-compose.testing.yml up -d

# Data will be recreated automatically
```

---

## Summary

**Before (With Auth):**
- ❌ Single URL: `http://localhost:9580/mcp/`
- ❌ Different auth tokens for each tenant
- ❌ Complex Newton configuration

**Now (No Auth):**
- ✅ Three URLs: 9580 (ESPN), 9581 (CNN), 9582 (NYT)
- ✅ No authentication required
- ✅ Simple Newton configuration

**Perfect for:**
- Initial Newton integration testing
- Demo scenarios
- Development workflows
- Learning AdCP protocol

---

**Status**: ✅ **READY FOR TESTING**

All three sales agents are running without authentication, each on a unique port, ready for Newton integration!


