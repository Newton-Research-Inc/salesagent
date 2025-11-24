# Newton → Sales Agent Connection Debugging

## Current Status

❌ **Problem**: Newton getting "No route to host" when trying to connect to sales agent task IP `10.118.143.32:9580`

✅ **Confirmed Working**:
- Security group has correct ingress rule (10.118.0.0/16 → ports 9580-9591)
- Services are listening on correct ports (9580, 9501, 9591)
- All three ECS services (ESPN, CNN, NYT) are running

## Root Cause Analysis

The "No route to host" error despite correct security groups suggests **Network ACL** or **Route Table** issues.

## Diagnostic Steps

### 1. Check if Newton can reach the ALB (public endpoint)

From Newton's server:
```bash
# Test ALB health endpoint (should work - goes through internet gateway)
curl -v http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/health
```

If this **works**, it confirms:
- Newton has internet access
- ALB is reachable
- Security groups allow ALB → ECS traffic

If this **fails**, there's a broader network issue.

### 2. Check Network ACLs for ECS subnets

```bash
# Get the Network ACL for the ECS subnets
SUBNET_ID="subnet-065023c1336d4c9f4"  # One of the ECS task subnets

NACL_ID=$(aws ec2 describe-network-acls \
  --region us-east-1 \
  --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
  --query 'NetworkAcls[0].NetworkAclId' \
  --output text)

echo "Network ACL: $NACL_ID"

# Check for DENY rules
aws ec2 describe-network-acls \
  --network-acl-ids "$NACL_ID" \
  --region us-east-1 \
  --query 'NetworkAcls[0].Entries[]' \
  --output table
```

**Look for**:
- Any DENY rules blocking ports 9580-9591
- Any DENY rules blocking traffic from 10.118.141.0/24 (Newton's subnet)

### 3. Check Route Tables

```bash
# Get route table for ECS subnets
ROUTE_TABLE_ID=$(aws ec2 describe-route-tables \
  --region us-east-1 \
  --filters "Name=association.subnet-id,Values=$SUBNET_ID" \
  --query 'RouteTables[0].RouteTableId' \
  --output text)

echo "Route Table: $ROUTE_TABLE_ID"

# Check routes
aws ec2 describe-route-tables \
  --route-table-ids "$ROUTE_TABLE_ID" \
  --region us-east-1 \
  --query 'RouteTables[0].Routes[]' \
  --output table
```

**Look for**:
- Route for 10.118.0.0/16 → local (should exist)
- If missing, traffic can't reach other VPC subnets

### 4. Verify Newton's Subnet Configuration

From Newton's server:
```bash
# Check Newton's routing
ip route show

# Check if Newton can reach other private IPs in the VPC
ping 10.118.143.32  # ECS task IP
```

## Potential Fixes

### Fix 1: Add Network ACL Rule (If Blocking)

```bash
# Add explicit ALLOW for ports 9580-9591 from VPC
aws ec2 create-network-acl-entry \
  --network-acl-id "$NACL_ID" \
  --rule-number 90 \
  --protocol tcp \
  --port-range From=9580,To=9591 \
  --cidr-block 10.118.0.0/16 \
  --rule-action allow \
  --ingress \
  --region us-east-1

# Also add for outbound (egress)
aws ec2 create-network-acl-entry \
  --network-acl-id "$NACL_ID" \
  --rule-number 90 \
  --protocol tcp \
  --port-range From=1024,To=65535 \
  --cidr-block 10.118.0.0/16 \
  --rule-action allow \
  --egress \
  --region us-east-1
```

### Fix 2: Deploy to Public Subnets Instead

If Network ACLs are complex, deploy ECS tasks to public subnets:

In `terraform/environments/staging/main.tf`, change:
```terraform
# Change from private to public subnets
module "ecs_espn" {
  source = "../../modules/ecs"
  # ...
  private_subnet_ids = data.aws_subnets.public.ids  # Changed!
  # ...
}
```

Then `terraform apply`.

### Fix 3: Use ALB for Routing (Fallback)

If direct IP connection continues to fail, route through ALB:

Newton connects to: `http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com:8080/health`

This goes through public internet → ALB → ECS (proven path).

## Quick Test

**From Newton's server**, try these in order:

```bash
# Test 1: Can Newton reach the internet?
curl -v https://www.google.com

# Test 2: Can Newton reach the ALB?
curl -v http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com:8080/health

# Test 3: Can Newton reach the task IP directly?
curl -v http://10.118.143.32:9580/health

# Test 4: Can Newton reach OTHER private IPs in the VPC?
curl -v http://10.118.0.1  # VPC gateway
```

If Test 1 & 2 work but Test 3 fails → **Network ACL or routing issue**
If Test 1 fails → **Newton has no internet access**
If Test 2 fails → **ALB security group or health check issue**
If Test 3 works → **🎉 Connection is working!**

## Next Steps

1. Run the diagnostic steps above
2. Share the results of the "Quick Test" from Newton's server
3. Based on the results, we'll apply the appropriate fix

## Alternative: Switch to SSE Client Test

Newton's `fastmcp.Client` might not be compatible with our FastMCP server's SSE implementation. Let's test with a simple Python script from Newton's server:

```python
import requests

# Test basic HTTP endpoint
response = requests.get("http://10.118.143.32:9580/health", timeout=5)
print(f"Status: {response.status_code}")
print(f"Body: {response.text}")
```

If this works, the issue is with FastMCP's SSE transport, not the network.

