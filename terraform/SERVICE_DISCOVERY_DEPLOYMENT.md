# Service Discovery Deployment Guide

## Overview

AWS Service Discovery (Cloud Map) provides stable DNS names for your sales agents that **persist across deployments**. No more changing IPs!

## What Changed

### Before (Dynamic IPs)
```
ESPN: http://10.118.130.100:9580/mcp  ❌ Changes every deployment
CNN:  http://10.118.131.50:9580/mcp   ❌ Changes every deployment
NYT:  http://10.118.132.75:9580/mcp   ❌ Changes every deployment
```

### After (Stable DNS)
```
ESPN: http://espn.salesagent.local:9580/mcp  ✅ Never changes!
CNN:  http://cnn.salesagent.local:9580/mcp   ✅ Never changes!
NYT:  http://nyt.salesagent.local:9580/mcp   ✅ Never changes!
```

## Deployment Steps

### 1. Review Terraform Changes

```bash
cd terraform/environments/staging
terraform plan
```

Expected changes:
- Create `aws_service_discovery_private_dns_namespace.salesagent`
- Create 3x `aws_service_discovery_service.tenant` (ESPN, CNN, NYT)
- Modify 3x `aws_ecs_service.salesagent` (add service_registries)

### 2. Apply Terraform Changes

```bash
terraform apply
```

This will:
1. Create the `salesagent.local` DNS namespace in your VPC
2. Create service discovery entries for each tenant
3. Update ECS services to auto-register task IPs

**Note**: Existing tasks will be gracefully restarted to register with Service Discovery.

### 3. Verify DNS Resolution

From Newton or any instance in the VPC:

```bash
# Test DNS resolution
dig espn.salesagent.local +short
# Should return the task IP (e.g., 10.118.130.100)

dig cnn.salesagent.local +short
dig nyt.salesagent.local +short

# Test MCP connectivity
curl -i http://espn.salesagent.local:9580/health
curl -i http://cnn.salesagent.local:9580/health
curl -i http://nyt.salesagent.local:9580/health
```

### 4. Update Newton's MCP Configuration

#### Option A: Update DataConnector Config

Edit Newton's `nri-server/newton/mcp_integration/data_connectors.py`:

```python
SALES_AGENT_SERVERS = {
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
```

#### Option B: Use Helper Script

```bash
# Show DNS names and Newton config
./get_dns_names.sh
```

### 5. Test Newton Connection

```bash
cd /path/to/newton/nri-server
python -m newton.mcp_integration.test_mcp_connection
```

Expected output:
```
✅ Connected to espn_sales_agent
✅ Discovered tools: get_products, create_media_buy, sync_creatives...
✅ Connected to cnn_sales_agent
✅ Discovered tools: get_products, create_media_buy, sync_creatives...
✅ Connected to nyt_sales_agent
✅ Discovered tools: get_products, create_media_buy, sync_creatives...
```

## How It Works

### Service Discovery Architecture

```
┌─────────────────────────────────────────────────────┐
│ VPC (Newton's VPC)                                  │
│                                                     │
│  ┌───────────────────────────────────────────┐    │
│  │ AWS Cloud Map (salesagent.local)          │    │
│  │                                           │    │
│  │  espn.salesagent.local → 10.118.130.100  │    │
│  │  cnn.salesagent.local  → 10.118.131.50   │    │
│  │  nyt.salesagent.local  → 10.118.132.75   │    │
│  └───────────────────────────────────────────┘    │
│           ▲                        ▲               │
│           │ registers              │ resolves      │
│           │                        │               │
│  ┌────────┴────────┐      ┌────────┴──────┐       │
│  │ ECS Tasks       │      │ Newton        │       │
│  │ (auto-register) │      │ (DNS client)  │       │
│  └─────────────────┘      └───────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Key Features

1. **Automatic Registration**: ECS tasks automatically register their IPs when they start
2. **Automatic Deregistration**: IPs are removed when tasks stop
3. **Low TTL**: 10-second DNS cache means Newton picks up new IPs quickly
4. **Health-aware**: Only healthy tasks are returned by DNS queries
5. **Multi-value**: If you scale to multiple tasks, all healthy IPs are returned

## Troubleshooting

### DNS Not Resolving

```bash
# Check if namespace exists
aws servicediscovery list-namespaces --region us-east-1

# Check if services exist
aws servicediscovery list-services --region us-east-1

# Check service instances (registered IPs)
aws servicediscovery list-instances \
  --service-id <service-id> \
  --region us-east-1
```

### Newton Can't Connect

1. **Verify DNS resolution** from Newton's instance:
   ```bash
   dig espn.salesagent.local +short
   ```

2. **Check security group** allows Newton → ECS tasks:
   ```bash
   # Should see rule allowing 10.118.0.0/16 → 9580-9591
   aws ec2 describe-security-groups \
     --group-ids <ecs-security-group-id> \
     --region us-east-1
   ```

3. **Test direct connectivity**:
   ```bash
   # From Newton instance
   telnet espn.salesagent.local 9580
   ```

### Old IP Still Cached

DNS TTL is 10 seconds, so wait 10-15 seconds after deployment for Newton to pick up new IPs.

Force flush DNS cache (if needed):
```bash
# On Linux
sudo systemd-resolve --flush-caches

# On macOS
sudo dscacheutil -flushcache
```

## Rollback

If you need to rollback to direct IP connections:

1. **Remove service registries** from ECS service:
   ```bash
   cd terraform/environments/staging
   git revert <this-commit>
   terraform apply
   ```

2. **Update Newton** to use IPs again:
   ```bash
   ./get_task_ips.sh
   # Update Newton config with IPs
   ```

## Cost

Service Discovery adds **$0.50/month per namespace + $0.10/month per service**:
- 1 namespace (`salesagent.local`): $0.50/month
- 3 services (espn, cnn, nyt): $0.30/month
- **Total: $0.80/month** (less than $1!)

Worth it for stable DNS names! 🎉

## Next Steps

After successful deployment:
1. ✅ Update Newton's MCP configuration to use DNS names
2. ✅ Test media buy workflow with all three agents
3. ✅ Enjoy never updating IPs again! 🚀

