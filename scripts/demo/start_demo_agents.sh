#!/bin/bash
set -e

echo "🚀 Starting AdCP Sales Agent Demo Environment"
echo "=============================================="
echo ""

# Change to the salesagent directory
cd "$(dirname "$0")/../.."

# Step 1: Start Docker Compose services
echo "📦 Step 1: Starting Docker Compose services..."
docker-compose -f docker-compose.testing.yml up -d

# Step 2: Wait for services to be healthy
echo ""
echo "⏳ Step 2: Waiting for services to be healthy..."
echo "   This may take 30-60 seconds..."

# Function to check if a service is healthy
check_health() {
    local url=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    return 1
}

# Check ESPN agent
echo -n "   ESPN agent (9580): "
if check_health "http://localhost:9580/health"; then
    echo " ✅"
else
    echo " ❌ Failed to start"
    exit 1
fi

# Check CNN agent
echo -n "   CNN agent (9581): "
if check_health "http://localhost:9581/health"; then
    echo " ✅"
else
    echo " ❌ Failed to start"
    exit 1
fi

# Check NYT agent
echo -n "   NYT agent (9582): "
if check_health "http://localhost:9582/health"; then
    echo " ✅"
else
    echo " ❌ Failed to start"
    exit 1
fi

# Step 3: Populate database with demo data
echo ""
echo "📊 Step 3: Populating database with demo data..."

docker-compose -f docker-compose.testing.yml exec -T espn-agent python << 'EOFPYTHON'
import sys
from datetime import UTC, datetime
sys.path.insert(0, '/app')

from sqlalchemy import select, delete
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant, Principal, CurrencyLimit, PropertyTag, Product, AuthorizedProperty, PricingOption, MediaBuy, MediaPackage

print("   Creating tenants, principals, products, pricing, and authorized properties...")

with get_db_session() as session:
    now = datetime.now(UTC)
    
    # Clean up any existing media buys (for fresh demo each time)
    print("   🧹 Cleaning up old campaigns...")
    from sqlalchemy import text
    # Delete packages first (foreign key constraint)
    session.execute(text("DELETE FROM media_packages WHERE media_buy_id IN (SELECT media_buy_id FROM media_buys WHERE tenant_id IN ('espn', 'cnn', 'nyt'))"))
    # Then delete media buys
    session.execute(text("DELETE FROM media_buys WHERE tenant_id IN ('espn', 'cnn', 'nyt')"))
    session.commit()
    
    # ESPN
    if not session.scalars(select(Tenant).filter_by(tenant_id='espn')).first():
        session.add(Tenant(tenant_id='espn', name='ESPN', subdomain='espn', ad_server='mock', is_active=True, billing_plan='standard', authorized_domains=['espn.com'], created_at=now, updated_at=now))
        session.add(CurrencyLimit(tenant_id='espn', currency_code='USD', min_package_budget=0, max_daily_package_spend=100000))
        session.add(PropertyTag(tenant_id='espn', tag_id='all_inventory', name='All ESPN Inventory', description='All inventory'))
        session.add(Principal(tenant_id='espn', principal_id='nike', name='Nike Inc.', platform_mappings={'mock': {'advertiser_id': 'nike'}}, access_token='adcp_espn_test'))
        session.add(Product(tenant_id='espn', product_id='espn_homepage_leaderboard', name='ESPN Homepage - Leaderboard', description='Premium ESPN homepage leaderboard', formats=[{'agent_url': 'http://localhost:9580/mcp/', 'id': 'display_728x90'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='espn', product_id='espn_live_game_sidebar', name='Live Game Sidebar', description='Sidebar during live games', formats=[{'agent_url': 'http://localhost:9580/mcp/', 'id': 'display_300x250'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='espn', product_id='espn_mobile_banner', name='Mobile App Banner', description='ESPN mobile app banner', formats=[{'agent_url': 'http://localhost:9580/mcp/', 'id': 'display_320x50'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(PricingOption(tenant_id='espn', product_id='espn_homepage_leaderboard', pricing_model='cpm', rate=25.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='espn', product_id='espn_live_game_sidebar', pricing_model='cpm', rate=20.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='espn', product_id='espn_mobile_banner', pricing_model='cpm', rate=15.00, currency='USD', is_fixed=True))
        session.add(AuthorizedProperty(tenant_id='espn', property_id='espn_main_site', property_type='website', name='ESPN Main Site', identifiers=[{'type': 'domain', 'value': 'espn.com'}], tags=['main', 'premium'], publisher_domain='espn.com', verification_status='verified', verification_checked_at=now))
        print("   ✅ ESPN: tenant, principal (Nike), 3 products with pricing, 1 authorized property")
    
    # CNN
    if not session.scalars(select(Tenant).filter_by(tenant_id='cnn')).first():
        session.add(Tenant(tenant_id='cnn', name='CNN', subdomain='cnn', ad_server='mock', is_active=True, billing_plan='standard', authorized_domains=['cnn.com'], created_at=now, updated_at=now))
        session.add(CurrencyLimit(tenant_id='cnn', currency_code='USD', min_package_budget=0, max_daily_package_spend=100000))
        session.add(PropertyTag(tenant_id='cnn', tag_id='all_inventory', name='All CNN Inventory', description='All inventory'))
        session.add(Principal(tenant_id='cnn', principal_id='cocacola', name='Coca-Cola', platform_mappings={'mock': {'advertiser_id': 'cocacola'}}, access_token='adcp_cnn_test'))
        session.add(Product(tenant_id='cnn', product_id='cnn_homepage_leaderboard', name='CNN Homepage - Leaderboard', description='Premium CNN homepage leaderboard', formats=[{'agent_url': 'http://localhost:9581/mcp/', 'id': 'display_728x90'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='cnn', product_id='cnn_article_skyscraper', name='Article Sidebar', description='Skyscraper in articles', formats=[{'agent_url': 'http://localhost:9581/mcp/', 'id': 'display_160x600'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='cnn', product_id='cnn_breaking_news_banner', name='Breaking News Banner', description='Billboard on breaking news', formats=[{'agent_url': 'http://localhost:9581/mcp/', 'id': 'display_970x250'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(PricingOption(tenant_id='cnn', product_id='cnn_homepage_leaderboard', pricing_model='cpm', rate=30.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='cnn', product_id='cnn_article_skyscraper', pricing_model='cpm', rate=28.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='cnn', product_id='cnn_breaking_news_banner', pricing_model='cpm', rate=35.00, currency='USD', is_fixed=True))
        session.add(AuthorizedProperty(tenant_id='cnn', property_id='cnn_main_site', property_type='website', name='CNN Main Site', identifiers=[{'type': 'domain', 'value': 'cnn.com'}], tags=['main', 'premium'], publisher_domain='cnn.com', verification_status='verified', verification_checked_at=now))
        print("   ✅ CNN: tenant, principal (Coca-Cola), 3 products with pricing, 1 authorized property")
    
    # NYT
    if not session.scalars(select(Tenant).filter_by(tenant_id='nyt')).first():
        session.add(Tenant(tenant_id='nyt', name='New York Times', subdomain='nyt', ad_server='mock', is_active=True, billing_plan='standard', authorized_domains=['nytimes.com'], created_at=now, updated_at=now))
        session.add(CurrencyLimit(tenant_id='nyt', currency_code='USD', min_package_budget=0, max_daily_package_spend=100000))
        session.add(PropertyTag(tenant_id='nyt', tag_id='all_inventory', name='All NYT Inventory', description='All inventory'))
        session.add(Principal(tenant_id='nyt', principal_id='apple', name='Apple Inc.', platform_mappings={'mock': {'advertiser_id': 'apple'}}, access_token='adcp_nyt_test'))
        session.add(Product(tenant_id='nyt', product_id='nyt_homepage_billboard', name='NYT Homepage - Billboard', description='Premium NYT homepage billboard', formats=[{'agent_url': 'http://localhost:9582/mcp/', 'id': 'display_970x250'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='nyt', product_id='nyt_article_rectangle', name='Article Inline', description='Rectangle in articles', formats=[{'agent_url': 'http://localhost:9582/mcp/', 'id': 'display_300x250'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(Product(tenant_id='nyt', product_id='nyt_opinion_leaderboard', name='Opinion Section', description='Leaderboard in opinion section', formats=[{'agent_url': 'http://localhost:9582/mcp/', 'id': 'display_728x90'}], targeting_template={'targeting': {}}, delivery_type='guaranteed', property_tags=['all_inventory'], countries=['US']))
        session.add(PricingOption(tenant_id='nyt', product_id='nyt_homepage_billboard', pricing_model='cpm', rate=40.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='nyt', product_id='nyt_article_rectangle', pricing_model='cpm', rate=35.00, currency='USD', is_fixed=True))
        session.add(PricingOption(tenant_id='nyt', product_id='nyt_opinion_leaderboard', pricing_model='cpm', rate=38.00, currency='USD', is_fixed=True))
        session.add(AuthorizedProperty(tenant_id='nyt', property_id='nyt_main_site', property_type='website', name='New York Times Main Site', identifiers=[{'type': 'domain', 'value': 'nytimes.com'}], tags=['main', 'premium'], publisher_domain='nytimes.com', verification_status='verified', verification_checked_at=now))
        print("   ✅ NYT: tenant, principal (Apple), 3 products with pricing, 1 authorized property")
    
    session.commit()
EOFPYTHON

# Step 4: Verify everything is working
echo ""
echo "🔍 Step 4: Verifying setup..."

# Check database
echo -n "   Database products: "
PRODUCT_COUNT=$(docker-compose -f docker-compose.testing.yml exec -T postgres psql -U adcp_user -d adcp -tAc "SELECT COUNT(*) FROM products;")
echo "$PRODUCT_COUNT ✅"

# Check each agent with curl
echo -n "   ESPN agent health: "
curl -sf http://localhost:9580/health > /dev/null && echo "✅" || echo "❌"

echo -n "   CNN agent health: "
curl -sf http://localhost:9581/health > /dev/null && echo "✅" || echo "❌"

echo -n "   NYT agent health: "
curl -sf http://localhost:9582/health > /dev/null && echo "✅" || echo "❌"

# Final summary
echo ""
echo "=============================================="
echo "✅ Demo environment ready!"
echo ""
echo "📡 Sales Agents:"
echo "   • ESPN:  http://localhost:9580/mcp/"
echo "   • CNN:   http://localhost:9581/mcp/"
echo "   • NYT:   http://localhost:9582/mcp/"
echo ""
echo "🔑 Authentication: DISABLED (test mode)"
echo "   No tokens needed for testing!"
echo ""
echo "📊 Demo Data:"
echo "   • 3 tenants (ESPN, CNN, NYT)"
echo "   • 3 principals (Nike, Coca-Cola, Apple)"
echo "   • 9 products (3 per tenant)"
echo "   • 9 pricing options (CPM: \$15-40)"
echo "   • 3 authorized properties (1 per tenant)"
echo ""
echo "🧪 Test Commands:"
echo "   # Get ESPN products:"
echo "   curl -X POST http://localhost:9580/mcp/ \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"get_products\",\"arguments\":{\"brief\":\"sports ads\"}},\"id\":1}'"
echo ""
echo "   # Check database:"
echo "   docker-compose -f docker-compose.testing.yml exec postgres psql -U adcp_user -d adcp -c 'SELECT tenant_id, COUNT(*) FROM products GROUP BY tenant_id;'"
echo ""
echo "Ready for Newton! 🚀"

