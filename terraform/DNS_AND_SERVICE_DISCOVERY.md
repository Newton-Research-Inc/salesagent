# DNS and Service Discovery Guide

## Overview

This guide covers two DNS configurations for the AdCP Sales Agent deployment:

1. **VPC-Internal Service Discovery** - Stable DNS within AWS VPC (for Newton ↔ Sales Agents)
2. **Public DNS** - External access via custom domain (for browser/API access)

---

## Part 1: VPC Service Discovery (Internal)

### What is Service Discovery?

AWS Service Discovery (Cloud Map) provides **stable DNS names** for ECS tasks within your VPC. This eliminates the need to track changing IP addresses.

### Before vs After

**Before (Dynamic IPs):**
```
ESPN: http://10.118.130.100:9580/mcp  ❌ Changes every deployment
CNN:  http://10.118.131.50:9580/mcp   ❌ Changes every deployment
NYT:  http://10.118.132.75:9580/mcp   ❌ Changes every deployment
Yahoo: http://10.118.133.25:9580/mcp  ❌ Changes every deployment
```

**After (Stable DNS):**
```
ESPN:  http://espn.salesagent.local:9580/mcp  ✅ Never changes!
CNN:   http://cnn.salesagent.local:9580/mcp   ✅ Never changes!
NYT:   http://nyt.salesagent.local:9580/mcp   ✅ Never changes!
Yahoo: http://yahoo.salesagent.local:9580/mcp ✅ Never changes!
```

### How It Works

1. **Private DNS Namespace**: `salesagent.local` (created once)
2. **Service Registrations**: Each ECS service registers under this namespace
3. **Automatic Updates**: When tasks restart, DNS automatically updates to new IP
4. **VPC-Only**: DNS names only resolve within the VPC (Newton must be in same VPC)

### Deployment

Service Discovery is already configured in Terraform. When you run `terraform apply`, it:

1. Creates `salesagent.local` DNS namespace
2. Registers each sales agent (ESPN, CNN, NYT, Yahoo)
3. Configures ECS tasks to auto-register on startup

### Verification

From Newton or any instance in the VPC:

```bash
# Test DNS resolution
dig espn.salesagent.local +short
# Should return task IP (e.g., 10.118.130.100)

# Test connectivity
curl http://espn.salesagent.local:9580/health
curl http://cnn.salesagent.local:9580/health
curl http://nyt.salesagent.local:9580/health
curl http://yahoo.salesagent.local:9580/health
```

### Newton MCP Configuration

Update Newton's MCP config to use stable DNS names:

```json
{
  "mcpServers": {
    "espn_sales_agent": {
      "url": "http://espn.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_espn_..."
      }
    },
    "cnn_sales_agent": {
      "url": "http://cnn.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_cnn_..."
      }
    },
    "nyt_sales_agent": {
      "url": "http://nyt.salesagent.local:9580/mcp",
      "headers": {
        "x-adcp-auth": "adcp_nyt_..."
      }
    },
    "yahoo_dsp": {
      "url": "http://yahoo.salesagent.local:9580/mcp"
    }
  }
}
```

### Troubleshooting Service Discovery

**Issue: DNS doesn't resolve**
- Ensure you're querying from within the VPC
- Service Discovery DNS is VPC-only (not public internet)
- Check namespace exists: `aws servicediscovery list-namespaces --region us-east-1`

**Issue: DNS returns old IP**
- Check ECS service health: Task might be unhealthy
- TTL is 10 seconds - wait a bit and retry
- Verify service registration: `aws servicediscovery list-services --region us-east-1`

**Issue: Multiple IPs returned**
- This is normal! Service Discovery uses `MULTIVALUE` routing
- Multiple tasks per service = multiple IPs
- Load balancing happens at TCP level

---

## Part 2: Public DNS Configuration

### Overview

For external access (browser, public API calls), you need to point your custom domain to the AWS Application Load Balancer.

### Prerequisites

- Domain name (e.g., `adcp-salesagent.com`)
- Access to DNS management for your domain
- ALB DNS name from Terraform output

### Get Your ALB DNS Name

```bash
cd terraform/environments/staging
terraform output alb_dns_name

# Example output:
# salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
```

### DNS Records to Create

You need **12 CNAME records** (3 services × 4 tenants):

| Subdomain | Type | Target | Purpose |
|-----------|------|--------|---------|
| `mcp-espn` | CNAME | `<ALB_DNS_NAME>` | ESPN MCP endpoint |
| `mcp-cnn` | CNAME | `<ALB_DNS_NAME>` | CNN MCP endpoint |
| `mcp-nyt` | CNAME | `<ALB_DNS_NAME>` | NYT MCP endpoint |
| `mcp-yahoo` | CNAME | `<ALB_DNS_NAME>` | Yahoo DSP MCP endpoint |
| `admin-espn` | CNAME | `<ALB_DNS_NAME>` | ESPN Admin UI |
| `admin-cnn` | CNAME | `<ALB_DNS_NAME>` | CNN Admin UI |
| `admin-nyt` | CNAME | `<ALB_DNS_NAME>` | NYT Admin UI |
| `admin-yahoo` | CNAME | `<ALB_DNS_NAME>` | Yahoo DSP Admin UI |
| `a2a-espn` | CNAME | `<ALB_DNS_NAME>` | ESPN A2A endpoint |
| `a2a-cnn` | CNAME | `<ALB_DNS_NAME>` | CNN A2A endpoint |
| `a2a-nyt` | CNAME | `<ALB_DNS_NAME>` | NYT A2A endpoint |
| `a2a-yahoo` | CNAME | `<ALB_DNS_NAME>` | Yahoo DSP A2A endpoint |

### DNS Configuration by Provider

#### AWS Route 53

```bash
# Get your hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='adcp-salesagent.com.'].Id" \
  --output text)

# Get ALB DNS from Terraform
ALB_DNS=$(cd terraform/environments/staging && terraform output -raw alb_dns_name)

# Create records (example for mcp-espn)
aws route53 change-resource-record-sets --hosted-zone-id $ZONE_ID --change-batch '{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "mcp-espn.adcp-salesagent.com",
      "Type": "CNAME",
      "TTL": 300,
      "ResourceRecords": [{"Value": "'$ALB_DNS'"}]
    }
  }]
}'

# Repeat for all 12 subdomains...
```

#### Cloudflare

1. Go to https://dash.cloudflare.com
2. Select your account and domain
3. Click "DNS" → "Add record"
4. For each subdomain:
   - **Type**: CNAME
   - **Name**: `mcp-espn` (subdomain only)
   - **Target**: `<ALB_DNS_NAME>`
   - **TTL**: Auto
   - **Proxy status**: DNS only (gray cloud)

#### Other Providers

1. Log into your DNS provider
2. Find "DNS Management" or "DNS Records"
3. Create CNAME record:
   - **Name/Host**: `mcp-espn`
   - **Type**: CNAME
   - **Value/Target**: `<ALB_DNS_NAME>`
   - **TTL**: 300

### SSL/TLS Certificates

**Option A: AWS Certificate Manager (Recommended)**

```bash
# Request certificate
aws acm request-certificate \
  --domain-name "*.adcp-salesagent.com" \
  --validation-method DNS \
  --region us-east-1

# ACM will provide DNS validation records - add them to your DNS
# Once validated, certificate will auto-renew
```

**Option B: Let's Encrypt + Cloudflare**

If using Cloudflare, enable:
- SSL/TLS → Full (strict)
- Always Use HTTPS
- Automatic HTTPS Rewrites

### Verification

After DNS propagates (5-30 minutes):

```bash
# Test DNS resolution
dig mcp-espn.adcp-salesagent.com +short
# Should return ALB DNS name or IP

# Test MCP endpoints
curl https://mcp-espn.adcp-salesagent.com/health
curl https://mcp-cnn.adcp-salesagent.com/health
curl https://mcp-nyt.adcp-salesagent.com/health
curl https://mcp-yahoo.adcp-salesagent.com/health

# Test Admin UI (in browser)
open https://admin-espn.adcp-salesagent.com
open https://admin-cnn.adcp-salesagent.com
open https://admin-nyt.adcp-salesagent.com
open https://admin-yahoo.adcp-salesagent.com
```

### Troubleshooting Public DNS

**Issue: DNS not resolving**
- Wait 5-30 minutes for propagation
- Check DNS with: `dig mcp-espn.adcp-salesagent.com`
- Verify CNAME created correctly in DNS provider
- Clear local DNS cache: `sudo dscacheutil -flushcache` (macOS)

**Issue: SSL certificate errors**
- Ensure certificate includes all subdomains (wildcard: `*.adcp-salesagent.com`)
- Verify certificate is validated in ACM console
- Check ALB listener is configured for HTTPS (port 443)

**Issue: "502 Bad Gateway"**
- ECS tasks may not be healthy
- Check ECS service: `aws ecs describe-services --cluster salesagent-espn --services salesagent-espn`
- Check target group health in ALB console
- Verify security groups allow ALB → ECS traffic

**Issue: Wrong tenant showing**
- ALB routes by subdomain (`Host` header)
- Verify `ADCP_TEST_TENANT_ID` environment variable matches subdomain prefix
- Check ALB listener rules in AWS console

---

## Quick Reference

### Service Discovery (Internal VPC)

```bash
# DNS Format
<tenant>.salesagent.local:9580

# Examples
espn.salesagent.local:9580
cnn.salesagent.local:9580
nyt.salesagent.local:9580
yahoo.salesagent.local:9580
```

**Use for:** Newton ↔ Sales Agents (within VPC)

### Public DNS (External Access)

```bash
# DNS Format
<service>-<tenant>.adcp-salesagent.com

# MCP Examples
mcp-espn.adcp-salesagent.com
mcp-cnn.adcp-salesagent.com
mcp-nyt.adcp-salesagent.com
mcp-yahoo.adcp-salesagent.com

# Admin UI Examples
admin-espn.adcp-salesagent.com
admin-cnn.adcp-salesagent.com
admin-nyt.adcp-salesagent.com
admin-yahoo.adcp-salesagent.com

# A2A Examples
a2a-espn.adcp-salesagent.com
a2a-cnn.adcp-salesagent.com
a2a-nyt.adcp-salesagent.com
a2a-yahoo.adcp-salesagent.com
```

**Use for:** Browser access, external API calls, public demos

---

## Summary

- **Service Discovery**: Stable DNS within VPC, automatic, no configuration needed after Terraform apply
- **Public DNS**: Requires manual CNAME records pointing to ALB, enables external access
- **Both work simultaneously**: Use Service Discovery for Newton, Public DNS for demos/admin

Choose the right DNS based on your use case!

