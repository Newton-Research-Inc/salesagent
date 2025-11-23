# Path-Based Routing Configuration (No DNS Needed!)

**Updated**: November 23, 2025  
**Change**: Switched from host-based to path-based routing  
**Reason**: Newton is on same VPC, no need for custom DNS  

---

## 🎯 New URL Structure

Newton can now access all sales agents using the ALB DNS directly:

**Base URL**: `http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com`

### ESPN Sales Agent
- **MCP**: `http://ALB-DNS/espn/mcp/`
- **Admin**: `http://ALB-DNS/espn/admin/`
- **A2A**: `http://ALB-DNS/espn/a2a/`

### CNN Sales Agent
- **MCP**: `http://ALB-DNS/cnn/mcp/`
- **Admin**: `http://ALB-DNS/cnn/admin/`
- **A2A**: `http://ALB-DNS/cnn/a2a/`

### NYT Sales Agent
- **MCP**: `http://ALB-DNS/nyt/mcp/`
- **Admin**: `http://ALB-DNS/nyt/admin/`
- **A2A**: `http://ALB-DNS/nyt/a2a/`

---

## 📋 Newton Configuration

Update Newton's MCP client configuration:

```json
{
  "espn_sales_agent": {
    "url": "http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  },
  "cnn_sales_agent": {
    "url": "http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/cnn/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  },
  "nyt_sales_agent": {
    "url": "http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/nyt/mcp/",
    "auth": {
      "type": "bearer",
      "token": "test-token"
    }
  }
}
```

---

## 🔧 ALB Routing Rules

**Path Pattern Matching**:

| Priority | Path Pattern | Target | Port |
|----------|-------------|--------|------|
| 100 | `/*/mcp`, `/*/mcp/*` | MCP Target Group | 9580 |
| 200 | `/*/admin`, `/*/admin/*` | Admin Target Group | 9501 |
| 300 | `/*/a2a`, `/*/a2a/*` | A2A Target Group | 9591 |

**Wildcard `*` matches**:
- `espn`
- `cnn`
- `nyt`

This allows for future expansion (e.g., adding `wsj`, `forbes`, etc.) without ALB changes.

---

## ✅ Benefits of Path-Based Routing

1. **No DNS Required**: Use ALB's AWS-provided DNS directly
2. **No Host Headers**: Cleaner, more intuitive URLs
3. **VPC-Native**: Perfect for internal-only access
4. **Flexible**: Easy to add new tenants (just add path prefix)
5. **Cost-Efficient**: No Route 53 hosted zone needed (~$0.50/month saved)

---

## 🚀 Applying the Change

After refreshing AWS SSO credentials:

```bash
cd /Users/danfinkel/github/opensource/salesagent/terraform/environments/staging
terraform apply -var="db_password=SalesAgent2024Demo!" -var="domain_name=adcp-salesagent.com"
```

**What will be updated**:
- ✏️ ALB Listener Rule: MCP (priority 100)
- ✏️ ALB Listener Rule: Admin (priority 200)
- ✏️ ALB Listener Rule: A2A (priority 300)

**Resources unchanged**: 26/29 (ALB, RDS, ECS, Security Groups all stay the same)

**Downtime**: None (ALB updates are instant)

---

## 🧪 Testing

After applying the changes:

```bash
# Test MCP endpoints (once services are healthy)
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/mcp/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/cnn/mcp/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/nyt/mcp/health

# Test Admin UI
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/admin/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/cnn/admin/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/nyt/admin/health

# Test A2A
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/a2a/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/cnn/a2a/health
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/nyt/a2a/health
```

**Expected Response** (once database is initialized):
- **Currently**: `503 Service Unavailable` (ECS tasks unhealthy, database not initialized)
- **After DB Init**: `200 OK` or `404 Not Found` (depends on /health endpoint implementation)

---

## 📝 Next Steps

1. ✅ **Refresh AWS SSO credentials**: `aws sso login`
2. ✅ **Apply Terraform changes**: Update ALB routing rules
3. ⏭️ **Initialize database**: Create schema and demo data
4. ⏭️ **Test endpoints**: Verify all 9 paths work
5. ⏭️ **Configure Newton**: Update MCP client with new URLs

---

## 🔍 Troubleshooting

### Issue: 404 on all paths
**Cause**: Path pattern not matching  
**Check**: Ensure paths start with `/espn/`, `/cnn/`, or `/nyt/`  
**Wrong**: `/mcp/espn/`  
**Right**: `/espn/mcp/`

### Issue: 503 Service Unavailable
**Cause**: ECS tasks unhealthy (this is expected until database is initialized)  
**Check**: 
```bash
aws ecs describe-services --cluster salesagent-staging --services salesagent-staging --region us-east-1 --query 'services[0].{Running:runningCount,Desired:desiredCount}'
```

### Issue: Connection timeout
**Cause**: Security group blocking traffic  
**Check**: Ensure Newton's security group allows outbound to ALB  
**Verify**: ALB security group allows inbound from Newton's security group

---

**Status**: ALB configuration updated locally  
**Action Required**: Refresh AWS SSO and apply Terraform changes  
**Impact**: Zero downtime, instant routing update  
**Next**: Database initialization

