#!/bin/bash

echo "📊 Checking for active campaigns..."
echo ""

# Execute Python script inside the espn-agent container to query campaigns
docker-compose -f docker-compose.testing.yml exec -T espn-agent python << 'EOFPYTHON'
import sys
from datetime import UTC, datetime
sys.path.insert(0, '/app')

from sqlalchemy import select, func
from src.core.database.database_session import get_db_session
from src.core.database.models import MediaBuy, MediaPackage

with get_db_session() as session:
    # Get all media buys
    stmt = select(MediaBuy).order_by(MediaBuy.created_at.desc())
    media_buys = session.scalars(stmt).all()
    
    if not media_buys:
        print("✅ No campaigns found in database")
        sys.exit(0)
    
    print(f"Found {len(media_buys)} campaign(s):\n")
    print("=" * 100)
    
    for buy in media_buys:
        # Get packages for this media buy
        pkg_stmt = select(MediaPackage).where(MediaPackage.media_buy_id == buy.media_buy_id)
        packages = session.scalars(pkg_stmt).all()
        
        # Calculate totals
        total_budget = sum(float(pkg.budget or 0) for pkg in packages)
        total_impressions = sum(pkg.package_config.get('impressions', 0) for pkg in packages)
        
        # Determine status emoji
        status_emoji = {
            'pending': '⏳',
            'needs_creatives': '🎨',
            'ready': '✅',
            'in_progress': '▶️',
            'completed': '✔️',
            'paused': '⏸️',
            'cancelled': '❌',
            'failed': '⛔'
        }.get(buy.status, '❓')
        
        print(f"\n{status_emoji} Campaign: {buy.buyer_ref}")
        print(f"   Media Buy ID: {buy.media_buy_id}")
        print(f"   Publisher: {buy.tenant_id.upper()}")
        print(f"   Advertiser: {buy.advertiser_name}")
        print(f"   Status: {buy.status}")
        print(f"   Dates: {buy.start_date} to {buy.end_date}")
        print(f"   Budget: ${total_budget:,.2f} USD")
        print(f"   Impressions: {total_impressions:,}")
        print(f"   Created: {buy.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if packages:
            print(f"\n   📦 Packages ({len(packages)}):")
            for i, pkg in enumerate(packages, 1):
                pkg_config = pkg.package_config
                impressions = pkg_config.get('impressions', 0)
                product_id = pkg_config.get('product_id', 'Unknown')
                status = pkg_config.get('status', 'Unknown')
                
                print(f"      {i}. {pkg.package_id}")
                print(f"         Product: {product_id}")
                print(f"         Budget: ${float(pkg.budget or 0):,.2f}")
                print(f"         Impressions: {impressions:,}")
                print(f"         Status: {status}")
                
                # Show delivery stats if available
                delivery_stats = pkg_config.get('delivery_stats')
                if delivery_stats:
                    delivered = delivery_stats.get('impressions_delivered', 0)
                    pct = (delivered / impressions * 100) if impressions > 0 else 0
                    print(f"         Delivered: {delivered:,} ({pct:.1f}%)")
                    if delivery_stats.get('budget_spent'):
                        print(f"         Spent: ${float(delivery_stats['budget_spent']):,.2f}")
        
        print("\n" + "-" * 100)
    
    # Summary statistics
    print(f"\n📈 Summary:")
    print(f"   Total campaigns: {len(media_buys)}")
    
    # Count by status
    status_counts = {}
    for buy in media_buys:
        status_counts[buy.status] = status_counts.get(buy.status, 0) + 1
    
    print(f"   By status:")
    for status, count in sorted(status_counts.items()):
        emoji = {
            'pending': '⏳',
            'needs_creatives': '🎨',
            'ready': '✅',
            'in_progress': '▶️',
            'completed': '✔️',
            'paused': '⏸️',
            'cancelled': '❌',
            'failed': '⛔'
        }.get(status, '❓')
        print(f"      {emoji} {status}: {count}")
    
    # Count by tenant
    tenant_counts = {}
    for buy in media_buys:
        tenant_counts[buy.tenant_id] = tenant_counts.get(buy.tenant_id, 0) + 1
    
    print(f"   By publisher:")
    for tenant, count in sorted(tenant_counts.items()):
        print(f"      📰 {tenant.upper()}: {count}")

EOFPYTHON

echo ""
echo "✅ Check complete!"

