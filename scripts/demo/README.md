# Demo Environment Scripts

Quick-start scripts for running the AdCP Sales Agent demo environment with three pre-configured publishers (ESPN, CNN, NYT).

## Quick Start

### Start Everything

```bash
./scripts/demo/start_demo_agents.sh
```

This will:
1. ✅ Start Docker Compose services (3 sales agents + PostgreSQL)
2. ✅ Wait for all services to be healthy
3. ✅ Populate database with demo data:
   - 3 tenants (ESPN, CNN, NYT)
   - 3 principals (Nike, Coca-Cola, Apple)
   - 9 products (3 per tenant)
4. ✅ Verify everything is working

**Output**: You'll see a summary with URLs, authentication status, and test commands.

### Stop Everything

```bash
./scripts/demo/stop_demo_agents.sh
```

This will cleanly stop all Docker Compose services.

### Check Active Campaigns

```bash
./scripts/demo/check_campaigns.sh
```

This will display all active campaigns in the database with detailed information:
- Campaign status and dates
- Budget and impression goals
- Package details
- Delivery statistics (if available)
- Summary by status and publisher

**When to use**:
- After Newton creates a campaign
- To verify campaign details
- To monitor delivery progress
- Before cleaning campaigns

### Clean Up Campaigns

```bash
./scripts/demo/clean_campaigns.sh
```

This will delete all media buys and packages for demo tenants (ESPN, CNN, NYT), giving Newton a fresh database for testing campaign creation.

**When to use**:
- Before testing Newton's campaign creation flow
- After a test run to reset the database
- When Newton gets confused by duplicate campaigns

---

## What Gets Created

### Sales Agents (MCP Servers)

| Publisher | URL | Port | Tenant ID | Principal | Token (not needed) |
|-----------|-----|------|-----------|-----------|-------------------|
| **ESPN** | http://localhost:9580/mcp/ | 9580 | `espn` | Nike Inc. | `adcp_espn_test` |
| **CNN** | http://localhost:9581/mcp/ | 9581 | `cnn` | Coca-Cola | `adcp_cnn_test` |
| **NYT** | http://localhost:9582/mcp/ | 9582 | `nyt` | Apple Inc. | `adcp_nyt_test` |

### Products

**ESPN:**
- `espn_homepage_leaderboard` - Premium ESPN homepage leaderboard (728x90)
- `espn_live_game_sidebar` - Sidebar during live games (300x250)
- `espn_mobile_banner` - Mobile app banner (320x50)

**CNN:**
- `cnn_homepage_leaderboard` - Premium CNN homepage leaderboard (728x90)
- `cnn_article_skyscraper` - Skyscraper in articles (160x600)
- `cnn_breaking_news_banner` - Billboard on breaking news (970x250)

**NYT:**
- `nyt_homepage_billboard` - Premium NYT homepage billboard (970x250)
- `nyt_article_rectangle` - Rectangle in articles (300x250)
- `nyt_opinion_leaderboard` - Leaderboard in opinion section (728x90)

---

## Test Commands

### Test with curl

```bash
# Get ESPN products
curl -X POST http://localhost:9580/mcp/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_products","arguments":{"brief":"sports ads"}},"id":1}'

# Get CNN products
curl -X POST http://localhost:9581/mcp/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_products","arguments":{"brief":"news ads"}},"id":1}'

# Get NYT products
curl -X POST http://localhost:9582/mcp/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_products","arguments":{"brief":"premium ads"}},"id":1}'
```

### Check Database

```bash
# Check products
docker-compose -f docker-compose.testing.yml exec postgres psql -U adcp_user -d adcp -c "SELECT tenant_id, COUNT(*) FROM products GROUP BY tenant_id;"

# Check media buys (after Newton creates some)
docker-compose -f docker-compose.testing.yml exec postgres psql -U adcp_user -d adcp -c "SELECT tenant_id, buyer_ref, status FROM media_buys;"
```

---

## Newton Integration

Newton should configure three MCP data connectors:

```json
{
  "espn_sales_agent": {
    "url": "http://localhost:9580/mcp/",
    "auth": "none"
  },
  "cnn_sales_agent": {
    "url": "http://localhost:9581/mcp/",
    "auth": "none"
  },
  "nyt_sales_agent": {
    "url": "http://localhost:9582/mcp/",
    "auth": "none"
  }
}
```

**Note**: Authentication is disabled in test mode. No tokens needed!

---

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
lsof -i :9580  # ESPN
lsof -i :9581  # CNN
lsof -i :9582  # NYT
lsof -i :9532  # PostgreSQL

# Stop any existing containers
docker-compose -f docker-compose.testing.yml down
```

### Database is empty

```bash
# Re-run the start script (it's idempotent)
./scripts/demo/start_demo_agents.sh
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.testing.yml logs -f

# View specific service
docker-compose -f docker-compose.testing.yml logs -f espn-agent
docker-compose -f docker-compose.testing.yml logs -f cnn-agent
docker-compose -f docker-compose.testing.yml logs -f nyt-agent
```

---

## Files

- `start_demo_agents.sh` - Start all services and populate database
- `stop_demo_agents.sh` - Stop all services
- `check_campaigns.sh` - Display all active campaigns with details
- `clean_campaigns.sh` - Clean up all media buys for demo tenants
- `populate_demo_products.py` - Detailed product population script (optional)
- `../../docker-compose.testing.yml` - Docker Compose configuration
- `../../NEWTON_INTEGRATION.md` - Newton integration guide
- `../../TESTING_NO_AUTH.md` - No-auth testing guide

---

## Next Steps

1. ✅ Start the demo environment
2. ✅ Configure Newton's MCP connectors
3. ✅ Have Newton discover the tools (`get_products`, `create_media_buy`, etc.)
4. ✅ Run test campaigns (see `../../docs/demo/NEWTON_CAMPAIGN_BRIEFS.md`)
5. ✅ Check database for created media buys
6. ✅ Test delivery tracking with `get_media_buy_delivery`

Ready to go! 🚀

