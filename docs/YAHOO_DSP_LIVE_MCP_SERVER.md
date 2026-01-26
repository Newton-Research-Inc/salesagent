# Yahoo DSP Live MCP Server

**Real Yahoo DSP API Integration for Programmatic Advertising**

## Overview

The Yahoo DSP Live MCP server provides real-time integration with the Yahoo Demand-Side Platform API for programmatic advertising. Unlike the simulated Yahoo DSP adapter (used for demos/testing), this server connects to the actual Yahoo DSP API and creates real campaigns.

| Attribute | Value |
|-----------|-------|
| **Server URL** | `http://yahoo-live.salesagent.local:9580/mcp` |
| **Protocol** | MCP (Model Context Protocol) |
| **Adapter** | `yahoo_dsp_live` |
| **API Type** | Real Yahoo DSP API |
| **Status** | Production-ready with test mode safeguards |

---

## Key Features

### 1. Real API Integration
- Connects to Yahoo DSP Traffic API (`https://dspapi.admanagerplus.yahoo.com/traffic/`)
- Creates actual campaigns, lines, and ads in Yahoo DSP
- Retrieves real delivery and performance data

### 2. Test Mode Safeguards (Enabled by Default)
To safely test the integration without creating costly live campaigns:
- **PAUSED Status**: All campaigns/lines created as `PAUSED` (not `ACTIVE`)
- **Budget Cap**: Maximum budget capped at $5.00 per campaign
- **Name Prefix**: Campaign/line names prefixed with `[TEST]` for easy identification

### 3. Tool Filtering
Only exposes relevant tools for Yahoo DSP operations:
- **Core AdCP Tools**: `get_products`, `create_media_buy`, `get_media_buy_delivery`, etc.
- **Yahoo-Specific Tools**: `listDeals`, `createCampaign`, `getCampaignDelivery`, etc.

---

## Authentication

The Yahoo DSP Live server uses **OAuth2 Client Credentials Flow**:

```
┌─────────────┐         ┌───────────────────────────────────────┐
│ MCP Server  │  POST   │ https://id.b2b.yahooinc.com/identity/ │
│             │ ───────>│ oauth2/access_token                   │
│             │         │                                       │
│             │ <─────  │ { access_token: "...", expires_in }   │
└─────────────┘         └───────────────────────────────────────┘
```

**Required Credentials** (stored in AWS Secrets Manager):
| Secret | Description |
|--------|-------------|
| `yahoo_dsp_client_id` | OAuth client ID from Yahoo Account Manager |
| `yahoo_dsp_client_secret` | OAuth client secret from Yahoo Account Manager |
| `yahoo_dsp_seat_id` | Your Yahoo DSP seat (account) ID |
| `yahoo_dsp_advertiser_id` | Your Yahoo DSP advertiser ID |

**API Headers**:
```
X-Auth-Method: OAuth2
X-Auth-Token: <access_token>
```

---

## Available Tools

### Core AdCP Tools (11 tools)

| Tool | Description |
|------|-------------|
| `get_products` | List available advertising products |
| `list_creative_formats` | Get supported creative formats |
| `sync_creatives` | Upload creative assets |
| `list_creatives` | List uploaded creatives |
| `get_signals` | Get available targeting signals |
| `activate_signal` | Activate a targeting signal |
| `list_authorized_properties` | List authorized properties/domains |
| `create_media_buy` | Create new campaign (Yahoo Campaign + Lines) |
| `update_media_buy` | Update campaign (pause, resume, update budget) |
| `get_media_buy_delivery` | Get delivery/performance metrics |
| `update_performance_index` | Update performance index for optimization |

### Yahoo-Specific Tools (12 tools)

| Tool | Description |
|------|-------------|
| `listDeals` | List available PMP deals |
| `getDealDetails` | Get deal details |
| `createCampaign` | Create Yahoo DSP campaign directly |
| `createLine` | Create line within campaign |
| `createAd` | Create ad linking creative to line |
| `getCampaignDelivery` | Get campaign delivery metrics |
| `activateCampaign` | Activate a campaign |
| `registerDeal` | Register a PMP deal |
| `registerInnovidTag` | Register Innovid creative tag |
| `getAudienceSegments` | List audience segments |
| `Get_analytics_for_audiences_segment` | Get audience segment analytics |
| `clearYahooDemoData` | Clean up test campaigns |

---

## MCP Connection Configuration

### For Newton (AI Agent)

Add to Newton's MCP configuration:

```json
{
  "mcpServers": {
    "yahoo_dsp_live": {
      "url": "http://yahoo-live.salesagent.local:9580/mcp",
      "description": "Yahoo DSP LIVE - Real Yahoo DSP API integration",
      "headers": {
        "x-adcp-auth": "<your-principal-token>"
      }
    }
  }
}
```

**Note**: DNS `yahoo-live.salesagent.local` only resolves within the VPC.

### For Claude Desktop or Other MCP Clients

```json
{
  "mcpServers": {
    "yahoo_dsp_live": {
      "transport": "sse",
      "url": "http://yahoo-live.salesagent.local:9580/mcp/sse"
    }
  }
}
```

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         AWS VPC                                   │
│                                                                   │
│  ┌─────────────────┐    ┌───────────────────────────────────────┐ │
│  │     Newton      │───>│  ECS Service: salesagent-yahoo-live   │ │
│  │   (AI Agent)    │    │                                       │ │
│  │                 │    │  Container: salesagent:staging        │ │
│  └─────────────────┘    │                                       │ │
│          │              │  Environment:                         │ │
│          │              │    TENANT_ID=yahoo_live               │ │
│          │              │    ENABLED_TOOLS=core,yahoo           │ │
│          │              │    YAHOO_DSP_TEST_MODE=true           │ │
│          │              │                                       │ │
│          ▼              └───────────────────────────────────────┘ │
│  ┌─────────────────┐                    │                        │
│  │ Service Discovery│                    │                        │
│  │ yahoo-live.      │                    ▼                        │
│  │ salesagent.local │    ┌───────────────────────────────────────┐│
│  └─────────────────┘    │       Yahoo DSP API (External)        ││
│                          │   dspapi.admanagerplus.yahoo.com      ││
│                          └───────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

### ECS Configuration

| Parameter | Value |
|-----------|-------|
| **Cluster** | `salesagent-yahoo-live` |
| **Service** | `salesagent-yahoo-live` |
| **Port** | 9580 |
| **DNS** | `yahoo-live.salesagent.local` |
| **CPU** | 0.25 vCPU |
| **Memory** | 512 MB |

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `TENANT_ID` | `yahoo_live` | Tenant identifier |
| `PRINCIPAL_ID` | `yahoo_live_test_buyer` | Default principal |
| `ENABLED_TOOLS` | `core,yahoo` | Tool filtering |
| `YAHOO_DSP_TEST_MODE` | `true` | Test mode safeguards |

---

## Test Mode vs Production Mode

| Feature | Test Mode (Default) | Production Mode |
|---------|---------------------|-----------------|
| Campaign Status | `PAUSED` | `ACTIVE` |
| Max Budget | $5.00 | Unlimited |
| Name Prefix | `[TEST]` | None |
| Safe for Testing | ✅ Yes | ⚠️ Creates live ads |

### Enabling Production Mode

To disable test mode for production use:

1. **Terraform** (recommended):
   ```hcl
   # In terraform/environments/staging/main.tf
   yahoo_dsp_test_mode = "false"
   ```

2. **Direct Environment Variable**:
   ```bash
   YAHOO_DSP_TEST_MODE=false
   ```

**Warning**: Production mode creates ACTIVE campaigns that will serve real ads and incur costs.

---

## Usage Examples

### Example 1: List Available Products

**Request** (via Newton):
```
What products are available on Yahoo DSP Live?
```

**Newton calls**: `get_products`

**Response**:
```json
{
  "products": [
    {
      "product_id": "yahoo_display_audience",
      "name": "Audience-Targeted Display",
      "format": "728x90",
      "pricing": {
        "model": "cpm",
        "rate": 6.50,
        "is_fixed": false
      }
    }
  ]
}
```

### Example 2: Create Test Campaign

**Request** (via Newton):
```
Create a $5 test campaign for Nike running January 27-31, 2026
```

**Newton calls**: `create_media_buy`

**Response** (Test Mode):
```json
{
  "media_buy_id": "12345",
  "buyer_ref": "nike_jan_campaign",
  "packages": [
    {
      "package_id": "pkg_001",
      "status": "draft",
      "buyer_ref": "yahoo_line_67890"
    }
  ]
}
```

**In Yahoo DSP UI**: Campaign appears as `[TEST] Nike` with `PAUSED` status

### Example 3: Get Delivery Metrics

**Request** (via Newton):
```
How is campaign 12345 performing?
```

**Newton calls**: `get_media_buy_delivery`

**Response**:
```json
{
  "media_buy_id": "12345",
  "totals": {
    "impressions": 1500000,
    "clicks": 2250,
    "spend": 9750.00,
    "conversions": 45
  }
}
```

---

## Cleanup Test Data

To remove test campaigns created during testing:

**Via Newton**:
```
Clean up my Yahoo DSP test campaigns
```

**Newton calls**: `clearYahooDemoData` or `clean_demo_data`

**Manual Cleanup via API**:
You can also use the Jupyter notebook pattern:

```python
import requests

# Get campaigns
response = requests.get(
    "https://dspapi.admanagerplus.yahoo.com/traffic/campaigns",
    headers={"X-Auth-Method": "OAuth2", "X-Auth-Token": token},
    params={"advertiserId": "33364"}
)

# Filter test campaigns
test_campaigns = [c for c in response.json()["data"] if c["name"].startswith("[TEST]")]

# Delete each
for campaign in test_campaigns:
    requests.delete(
        f"https://dspapi.admanagerplus.yahoo.com/traffic/campaigns/{campaign['id']}",
        headers={"X-Auth-Method": "OAuth2", "X-Auth-Token": token}
    )
```

---

## Troubleshooting

### Issue: Authentication Failed

**Symptom**: 403 Forbidden from Yahoo DSP API

**Cause**: Invalid or expired OAuth credentials

**Fix**:
1. Verify secrets in AWS Secrets Manager
2. Check `yahoo_dsp_client_id` and `yahoo_dsp_client_secret` are correct
3. Verify credentials haven't expired with Yahoo Account Manager

### Issue: Campaign Creation Returns 500

**Symptom**: HTTP 500 from Yahoo Traffic API

**Possible Causes**:
- Invalid payload format (check required fields)
- Budget in wrong units (should be dollars, not cents)
- Missing timezone in campaign

**Debug**: Check CloudWatch logs for detailed error:
```bash
aws logs tail /ecs/salesagent-yahoo-live --follow --region us-east-1
```

### Issue: DNS Not Resolving

**Symptom**: `Could not resolve host: yahoo-live.salesagent.local`

**Cause**: Not in VPC with Service Discovery

**Fix**: Ensure client is in the same VPC as the ECS service

### Issue: Tools Not Available

**Symptom**: Newton says no tools detected

**Cause**: Tool filtering misconfigured

**Fix**: Verify `ENABLED_TOOLS=core,yahoo` in ECS task definition

---

## Comparison with Simulated Yahoo DSP

| Feature | Yahoo DSP (Simulated) | Yahoo DSP Live |
|---------|----------------------|----------------|
| **URL** | `yahoo.salesagent.local:9580` | `yahoo-live.salesagent.local:9580` |
| **Adapter** | `yahoo_dsp` | `yahoo_dsp_live` |
| **API Calls** | None (in-memory) | Real Yahoo DSP API |
| **Data Persistence** | Session only | Yahoo DSP platform |
| **Credentials Required** | No | Yes |
| **Cost** | Free | Real ad spend |
| **Use Case** | Demos, development | Production |

---

## API Reference

### Yahoo DSP Traffic API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/traffic/campaigns` | POST | Create campaign |
| `/traffic/campaigns/{id}` | GET | Get campaign |
| `/traffic/campaigns/{id}` | PUT | Update campaign |
| `/traffic/campaigns/{id}` | DELETE | Delete campaign |
| `/traffic/lines` | POST | Create line |
| `/traffic/lines/{id}` | GET/PUT | Get/update line |
| `/traffic/creatives` | POST | Upload creative |
| `/traffic/ads` | POST | Create ad |
| `/reporting/reports` | POST | Generate report |

### Yahoo DSP Object Mapping

| AdCP Concept | Yahoo DSP Object |
|--------------|------------------|
| Media Buy | Campaign |
| Package | Line |
| Creative | Creative + Ad |
| Delivery | Report |

---

## Related Documentation

- **Yahoo DSP Adapter README**: `src/adapters/yahoo_dsp/README.md`
- **Yahoo DSP Demo Guide**: `docs/demo/YAHOO_DSP_GUIDE.md`
- **Deployment Guide**: `terraform/DEPLOYMENT_GUIDE.md`
- **Yahoo DSP API Documentation**: https://help.yahooinc.com/dsp-api/docs/

---

## Changelog

### January 2026
- Initial production deployment
- JWT client assertion authentication
- Test mode safeguards (PAUSED campaigns, $5 budget cap)
- Environment-based tool filtering (`ENABLED_TOOLS=core,yahoo`)
- AWS ECS deployment with Service Discovery
