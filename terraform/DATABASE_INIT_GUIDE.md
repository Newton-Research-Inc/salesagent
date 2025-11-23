# Database Initialization Guide

**Database**: staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432  
**Status**: Empty (no schema, no data)  
**Goal**: Create schema + populate with ESPN, CNN, NYT demo data  

---

## 🔒 Security Context

The RDS database is in a **private subnet** and only accepts connections from ECS tasks (via security group `sg-0f648b2522a7df578`).

We need to temporarily allow your IP to connect for initialization.

---

## 📋 Step 1: Get Your Public IP

```bash
curl -s ifconfig.me
```

**Save this IP** - you'll need it for the security group rule.

---

## 📋 Step 2: Temporarily Allow Your IP

Run this command (replace `YOUR_IP` with the IP from Step 1):

```bash
# Add your IP to RDS security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr YOUR_IP/32 \
  --region us-east-1
```

**Example**:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr 203.0.113.45/32 \
  --region us-east-1
```

---

## 📋 Step 3: Test Database Connection

```bash
# Test connection (should connect successfully)
psql "postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# Once connected, type \q to quit
```

**If connection fails**, check:
1. Security group rule was added
2. RDS instance is in "available" state
3. Your local firewall allows outbound PostgreSQL

---

## 📋 Step 4: Run Migrations

From the salesagent directory:

```bash
cd /Users/danfinkel/github/opensource/salesagent

# Set database URL
export DATABASE_URL="postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# Run Alembic migrations to create schema
uv run alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Create initial tables
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, Add tenants table
...
```

---

## 📋 Step 5: Populate Demo Data

Run the initialization script:

```bash
# Still in /Users/danfinkel/github/opensource/salesagent
uv run python scripts/setup/init_database_ci.py
```

**This creates**:
- 3 Tenants: ESPN, CNN, NYT
- 3 Principals: Nike, Coca-Cola, Apple
- Products for each tenant (homepage leaderboards, sidebars, mobile banners)
- AuthorizedProperty records
- PricingOptions for each product
- CurrencyLimits (USD)

**Expected output**:
```
Creating tenant: espn
Creating tenant: cnn
Creating tenant: nyt
Creating principal: nike (for espn)
Creating principal: cocacola (for cnn)
Creating principal: apple (for nyt)
Creating products for espn...
Creating products for cnn...
Creating products for nyt...
✅ Database initialized successfully!
```

---

## 📋 Step 6: Verify Data

```bash
# Connect to database
psql "postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# Check tenants
SELECT tenant_id, name, subdomain FROM tenants;

# Check principals
SELECT principal_id, name, tenant_id FROM principals;

# Check products
SELECT product_id, name, tenant_id FROM products;

# Exit
\q
```

---

## 📋 Step 7: Remove Your IP (Security Cleanup)

**IMPORTANT**: Remove the temporary access rule:

```bash
# Get your IP again (in case it changed)
MY_IP=$(curl -s ifconfig.me)

# Remove your IP from RDS security group
aws ec2 revoke-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr ${MY_IP}/32 \
  --region us-east-1
```

**Why this matters**: Leaving your IP open is a security risk. The database should only be accessible from ECS tasks.

---

## 📋 Step 8: Restart ECS Service

Force ECS to restart with the new database:

```bash
# Force new deployment
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-staging \
  --force-new-deployment \
  --region us-east-1

# Watch service status
aws ecs describe-services \
  --cluster salesagent-staging \
  --services salesagent-staging \
  --region us-east-1 \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount}'
```

**Wait 2-3 minutes** for the new task to start and become healthy.

---

## ✅ Verification

After ECS tasks are healthy, test the endpoints:

```bash
# Test ESPN MCP endpoint
curl http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/mcp/health

# Should return: 200 OK (or 404 if /health endpoint doesn't exist)
# NOT: 503 Service Unavailable
```

---

## 🚨 Troubleshooting

### Issue: `psql: command not found`

Install PostgreSQL client:

**macOS**:
```bash
brew install postgresql@15
```

**Alternative**: Use Docker:
```bash
docker run -it --rm postgres:15 psql "postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"
```

### Issue: Connection timeout

**Causes**:
1. Security group rule not applied yet (wait 10-20 seconds)
2. Your local firewall blocking outbound port 5432
3. RDS instance not in "available" state

**Check RDS status**:
```bash
aws rds describe-db-instances \
  --db-instance-identifier staging-salesagent-db \
  --query 'DBInstances[0].DBInstanceStatus' \
  --output text
```

### Issue: Password authentication failed

Double-check the password:
- Password: `SalesAgent2024Demo!`
- Escape the `!` in shell commands or use single quotes

### Issue: `alembic upgrade head` fails

**Cause**: Alembic might not be finding migrations

**Fix**:
```bash
# Ensure you're in the correct directory
cd /Users/danfinkel/github/opensource/salesagent

# Check alembic.ini exists
ls -la alembic.ini

# Run with explicit config
uv run alembic -c alembic.ini upgrade head
```

### Issue: `init_database_ci.py` fails

**Common errors**:
1. **IntegrityError**: Data already exists (safe to ignore if rerunning)
2. **Connection error**: Database URL not set correctly

**Check**:
```bash
echo $DATABASE_URL
# Should output: postgresql://salesagent:...
```

---

## 📝 Quick Copy-Paste Sequence

```bash
# 1. Get your IP
MY_IP=$(curl -s ifconfig.me)
echo "Your IP: $MY_IP"

# 2. Allow your IP
aws ec2 authorize-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr ${MY_IP}/32 \
  --region us-east-1

# 3. Set database URL
export DATABASE_URL="postgresql://salesagent:SalesAgent2024Demo!@staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com:5432/salesagent"

# 4. Run migrations
cd /Users/danfinkel/github/opensource/salesagent
uv run alembic upgrade head

# 5. Populate data
uv run python scripts/setup/init_database_ci.py

# 6. Remove your IP (security cleanup)
aws ec2 revoke-security-group-ingress \
  --group-id sg-0f648b2522a7df578 \
  --protocol tcp \
  --port 5432 \
  --cidr ${MY_IP}/32 \
  --region us-east-1

# 7. Restart ECS service
aws ecs update-service \
  --cluster salesagent-staging \
  --service salesagent-staging \
  --force-new-deployment \
  --region us-east-1

# 8. Test endpoint (wait 2-3 minutes first)
curl -I http://salesagent-staging-alb-1925538097.us-east-1.elb.amazonaws.com/espn/mcp/health
```

---

**Status**: Ready for database initialization  
**Time**: ~10 minutes  
**Risk**: Low (temporary security group rule, removed after)  
**Next**: Configure Newton to use the new endpoints

