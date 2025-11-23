# DNS Configuration Guide for AdCP Sales Agent

**Target**: Point 9 subdomains to AWS Application Load Balancer  
**Domain**: adcp-salesagent.com  
**ALB DNS**: salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com  

---

## 📋 DNS Records to Create

Create **9 CNAME records** in your DNS provider:

### Record Details

| Subdomain | Type | Target | TTL |
|-----------|------|--------|-----|
| `mcp-espn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `mcp-cnn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `mcp-nyt` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `admin-espn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `admin-cnn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `admin-nyt` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `a2a-espn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `a2a-cnn` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |
| `a2a-nyt` | CNAME | `salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com` | 300 |

---

## 🔧 Step-by-Step Instructions

### Step 1: Find Your DNS Provider

**Where is `adcp-salesagent.com` hosted?**

Common providers:
- **Route 53** (AWS)
- **Cloudflare**
- **GoDaddy**
- **Namecheap**
- **Google Domains**
- **Other**

### Step 2: Access DNS Management

**Route 53** (AWS):
1. Go to: https://console.aws.amazon.com/route53
2. Click "Hosted zones"
3. Click on `adcp-salesagent.com`
4. Click "Create record"

**Cloudflare**:
1. Go to: https://dash.cloudflare.com
2. Select your account
3. Click on `adcp-salesagent.com`
4. Click "DNS" → "Add record"

**GoDaddy**:
1. Go to: https://dcc.godaddy.com/domains
2. Click on `adcp-salesagent.com`
3. Click "DNS" → "Add"

**Other Providers**: Look for "DNS Management" or "DNS Records"

### Step 3: Create Each Record

For **each** of the 9 subdomains, create a CNAME record:

**Example for `mcp-espn`**:
```
Name/Host: mcp-espn
Type: CNAME
Value/Target: salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
TTL: 300 (5 minutes)
```

**Repeat for all 9**:
- mcp-espn
- mcp-cnn
- mcp-nyt
- admin-espn
- admin-cnn
- admin-nyt
- a2a-espn
- a2a-cnn
- a2a-nyt

### Step 4: Wait for Propagation

⏱️ **Wait time**: 5-10 minutes (with TTL=300)

DNS changes need time to propagate across the internet.

---

## ✅ Verification

After waiting 5-10 minutes, test each record:

### Test with `dig` (macOS/Linux):
```bash
# Test ESPN MCP endpoint
dig mcp-espn.adcp-salesagent.com +short

# Expected output:
# salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
# <ALB-IP-address>
```

### Test with `nslookup` (all platforms):
```bash
nslookup mcp-espn.adcp-salesagent.com

# Expected output includes:
# Name: salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
```

### Test with `curl`:
```bash
# Test HTTP connectivity
curl -I http://mcp-espn.adcp-salesagent.com/health

# Expected: 404 (service not ready yet) or 503 (service starting)
# NOT EXPECTED: Connection refused, DNS resolution error
```

### Quick Test All Endpoints:
```bash
# Copy and paste this to test all 9 endpoints
for subdomain in mcp-espn mcp-cnn mcp-nyt admin-espn admin-cnn admin-nyt a2a-espn a2a-cnn a2a-nyt; do
  echo -n "Testing ${subdomain}.adcp-salesagent.com: "
  dig +short ${subdomain}.adcp-salesagent.com | grep -q "elb.amazonaws.com" && echo "✅ OK" || echo "❌ FAILED"
done
```

---

## 🚨 Troubleshooting

### Issue: "NXDOMAIN" or "not found"
**Cause**: DNS record not created or typo in name  
**Fix**: Double-check record name and save changes

### Issue: Points to wrong IP
**Cause**: Typo in target/value  
**Fix**: Edit record, ensure target is exactly:
```
salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com
```

### Issue: Still not working after 10 minutes
**Causes**:
1. DNS provider propagation delay (can be up to 48 hours for some)
2. Your local DNS cache

**Fix**:
```bash
# Flush local DNS cache (macOS)
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

# Flush local DNS cache (Linux)
sudo systemd-resolve --flush-caches

# Test with specific DNS server
dig @8.8.8.8 mcp-espn.adcp-salesagent.com +short
```

### Issue: Works with `dig` but not `curl`
**Cause**: This is expected! DNS is working, but:
- ECS tasks may not be healthy yet (database not initialized)
- ALB health checks failing

**Status**: DNS configuration is **complete** ✅  
**Next**: Database initialization (Step 2)

---

## 📝 Record Summary

After creating all records, you should be able to resolve:

**MCP Endpoints** (for Newton):
- http://mcp-espn.adcp-salesagent.com
- http://mcp-cnn.adcp-salesagent.com
- http://mcp-nyt.adcp-salesagent.com

**Admin UI** (for manual testing):
- http://admin-espn.adcp-salesagent.com
- http://admin-cnn.adcp-salesagent.com
- http://admin-nyt.adcp-salesagent.com

**A2A Endpoints** (for agent-to-agent):
- http://a2a-espn.adcp-salesagent.com
- http://a2a-cnn.adcp-salesagent.com
- http://a2a-nyt.adcp-salesagent.com

---

## 🎯 Quick Copy-Paste for Route 53 CLI

If you're using Route 53 and want to automate:

```bash
# Set variables
HOSTED_ZONE_ID="<your-hosted-zone-id>"  # Get from Route 53 console
ALB_DNS="salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com"

# Create all 9 records
for subdomain in mcp-espn mcp-cnn mcp-nyt admin-espn admin-cnn admin-nyt a2a-espn a2a-cnn a2a-nyt; do
  aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch "{
    \"Changes\": [{
      \"Action\": \"CREATE\",
      \"ResourceRecordSet\": {
        \"Name\": \"${subdomain}.adcp-salesagent.com\",
        \"Type\": \"CNAME\",
        \"TTL\": 300,
        \"ResourceRecords\": [{\"Value\": \"$ALB_DNS\"}]
      }
    }]
  }"
done
```

---

**Status**: DNS configuration guide ready  
**Action Required**: Create 9 CNAME records in your DNS provider  
**Time**: 5-10 minutes + propagation wait  
**Risk**: None (isolated to new domain)

