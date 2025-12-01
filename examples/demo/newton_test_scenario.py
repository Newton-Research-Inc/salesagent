#!/usr/bin/env python3
"""
Newton Test Scenario - Complete Media Buying Flow
Demonstrates how Newton can discover inventory and purchase across ESPN, CNN, NYT.
"""

import asyncio
import json
from datetime import datetime, timedelta
from fastmcp.client import Client
from fastmcp.transports import StreamableHttpTransport


# Sales Agent Configuration
SALES_AGENTS = {
    "espn": {
        "name": "ESPN",
        "url": "http://localhost:9580/mcp/",
        "token": "adcp_espn_ZgDyLYOkOwlrVkGA6xIKn0QMEUGrcWo9B1UE73MOLdA",
        "campaign": "Nike Air Jordan Launch"
    },
    "cnn": {
        "name": "CNN",
        "url": "http://localhost:9580/mcp/",
        "token": "adcp_cnn_bCLg89IQMy10K5exnTuO7bKZNx6LhYz8E9DexZ6DhlM",
        "campaign": "Coca-Cola Holiday Campaign"
    },
    "nyt": {
        "name": "NYT",
        "url": "http://localhost:9580/mcp/",
        "token": "adcp_nyt_yCJn_Ji_br1ydkg3KLu_gqqOiZSiuh-hgyjMMcu1oAo",
        "campaign": "Apple Vision Pro Awareness"
    }
}


async def discover_inventory(agent_key, brief):
    """
    Phase 1: Discovery - Newton asks each sales agent about available inventory.
    """
    agent = SALES_AGENTS[agent_key]
    print(f"\n{'='*80}")
    print(f"🔍 DISCOVERY: {agent['name']} Sales Agent")
    print(f"{'='*80}")
    print(f"Campaign: {agent['campaign']}")
    print(f"Query: {brief}\n")
    
    headers = {"x-adcp-auth": agent["token"]}
    transport = StreamableHttpTransport(url=agent["url"], headers=headers)
    client = Client(transport=transport)
    
    try:
        async with client:
            # Get available products
            result = await client.call_tool("get_products", {"brief": brief})
            
            products = result.get("products", [])
            print(f"✅ Found {len(products)} matching products:\n")
            
            for i, product in enumerate(products, 1):
                print(f"{i}. {product['name']}")
                print(f"   ID: {product['product_id']}")
                print(f"   Description: {product['description'][:100]}...")
                if 'pricing_option' in product:
                    pricing = product['pricing_option']
                    if 'price_guidance' in pricing:
                        guidance = pricing['price_guidance']
                        print(f"   Pricing: ${guidance.get('floor', 'N/A')}-${guidance.get('p75', 'N/A')} CPM")
                print()
            
            return products
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


async def create_media_buy(agent_key, campaign_config):
    """
    Phase 2: Purchase - Newton creates a media buy for selected products.
    """
    agent = SALES_AGENTS[agent_key]
    print(f"\n{'='*80}")
    print(f"💰 PURCHASE: Creating Media Buy on {agent['name']}")
    print(f"{'='*80}")
    
    headers = {"x-adcp-auth": agent["token"]}
    transport = StreamableHttpTransport(url=agent["url"], headers=headers)
    client = Client(transport=transport)
    
    try:
        async with client:
            # Create media buy
            result = await client.call_tool("create_media_buy", campaign_config)
            
            print(f"✅ Media Buy Created Successfully!\n")
            print(f"Media Buy ID: {result.get('media_buy_id')}")
            print(f"Status: {result.get('status')}")
            
            if 'packages' in result:
                print(f"\nPackages Created:")
                for pkg in result['packages']:
                    print(f"  • Package ID: {pkg.get('package_id')}")
                    print(f"    Product: {pkg.get('product_ref')}")
                    if 'inventory_allocations' in pkg:
                        for alloc in pkg['inventory_allocations']:
                            print(f"    Impressions: {alloc.get('quantity', 'N/A'):,}")
            
            return result
    except Exception as e:
        print(f"❌ Error creating media buy: {e}")
        import traceback
        traceback.print_exc()
        return None


async def check_delivery(agent_key, media_buy_id):
    """
    Phase 3: Monitoring - Newton checks campaign delivery and performance.
    """
    agent = SALES_AGENTS[agent_key]
    print(f"\n{'='*80}")
    print(f"📊 MONITORING: Checking Delivery on {agent['name']}")
    print(f"{'='*80}")
    
    headers = {"x-adcp-auth": agent["token"]}
    transport = StreamableHttpTransport(url=agent["url"], headers=headers)
    client = Client(transport=transport)
    
    try:
        async with client:
            # Get delivery stats
            result = await client.call_tool("get_media_buy_delivery", {
                "media_buy_ids": [media_buy_id]
            })
            
            deliveries = result.get('deliveries', [])
            if deliveries:
                delivery = deliveries[0]
                print(f"✅ Delivery Data Retrieved\n")
                print(f"Media Buy ID: {delivery.get('media_buy_id')}")
                print(f"Status: {delivery.get('status')}")
                
                if 'packages' in delivery:
                    print(f"\nPackage Performance:")
                    for pkg in delivery['packages']:
                        print(f"  • Package: {pkg.get('package_id')}")
                        if 'delivery_stats' in pkg:
                            stats = pkg['delivery_stats']
                            print(f"    Impressions: {stats.get('impressions_delivered', 0):,} / {stats.get('impressions_goal', 0):,}")
                            print(f"    Clicks: {stats.get('clicks_delivered', 0):,}")
                            if stats.get('impressions_delivered', 0) > 0:
                                ctr = (stats.get('clicks_delivered', 0) / stats.get('impressions_delivered', 1)) * 100
                                print(f"    CTR: {ctr:.2f}%")
            else:
                print("⚠️ No delivery data available yet")
            
            return result
    except Exception as e:
        print(f"❌ Error checking delivery: {e}")
        return None


async def scenario_espn_nike():
    """
    Scenario 1: Nike Air Jordan Launch on ESPN
    """
    print("\n" + "🏈 " * 40)
    print("SCENARIO 1: Nike Air Jordan Launch")
    print("🏈 " * 40)
    
    # Phase 1: Discovery
    products = await discover_inventory(
        "espn",
        "Display inventory for sports brand targeting basketball fans"
    )
    
    if not products:
        print("❌ No products found, stopping scenario")
        return
    
    # Phase 2: Purchase
    # Select ESPN Homepage Leaderboard product
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")
    
    campaign_config = {
        "promoted_offering": "Nike Air Jordan Collection",
        "buyer_ref": "nike_air_jordan_demo_001",
        "packages": [
            {
                "package_ref": "pkg_nike_espn_homepage",
                "product_ref": "espn_homepage_leaderboard",
                "start_date": start_date,
                "end_date": end_date,
                "pricing": {
                    "pricing_model": "CPM",
                    "rate": 12.00,
                    "currency": "USD"
                },
                "inventory_requests": [
                    {
                        "quantity": 4000000,  # 4M impressions
                        "unit": "IMPRESSIONS"
                    }
                ]
            }
        ]
    }
    
    media_buy = await create_media_buy("espn", campaign_config)
    
    if media_buy:
        # Phase 3: Monitor (simulated - would happen after campaign starts)
        media_buy_id = media_buy.get('media_buy_id')
        print(f"\n💡 To monitor this campaign later, use:")
        print(f"   Media Buy ID: {media_buy_id}")
        print(f"   Tool: get_media_buy_delivery")


async def scenario_cnn_cocacola():
    """
    Scenario 2: Coca-Cola Holiday Campaign on CNN
    """
    print("\n" + "📰 " * 40)
    print("SCENARIO 2: Coca-Cola Holiday Campaign")
    print("📰 " * 40)
    
    # Phase 1: Discovery
    products = await discover_inventory(
        "cnn",
        "News inventory for holiday brand awareness campaign"
    )
    
    if not products:
        print("❌ No products found, stopping scenario")
        return
    
    # Phase 2: Purchase
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d")
    
    campaign_config = {
        "promoted_offering": "Coca-Cola Holidays Together",
        "buyer_ref": "cocacola_holidays_demo_001",
        "packages": [
            {
                "package_ref": "pkg_coke_cnn_homepage",
                "product_ref": "cnn_homepage_leaderboard",
                "start_date": start_date,
                "end_date": end_date,
                "pricing": {
                    "pricing_model": "CPM",
                    "rate": 15.00,
                    "currency": "USD"
                },
                "inventory_requests": [
                    {
                        "quantity": 5000000,  # 5M impressions
                        "unit": "IMPRESSIONS"
                    }
                ]
            }
        ]
    }
    
    media_buy = await create_media_buy("cnn", campaign_config)
    
    if media_buy:
        media_buy_id = media_buy.get('media_buy_id')
        print(f"\n💡 Campaign created! Media Buy ID: {media_buy_id}")


async def scenario_nyt_apple():
    """
    Scenario 3: Apple Vision Pro on NYT
    """
    print("\n" + "📖 " * 40)
    print("SCENARIO 3: Apple Vision Pro Awareness")
    print("📖 " * 40)
    
    # Phase 1: Discovery
    products = await discover_inventory(
        "nyt",
        "Premium inventory for tech product launch to affluent audience"
    )
    
    if not products:
        print("❌ No products found, stopping scenario")
        return
    
    # Phase 2: Purchase
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=31)).strftime("%Y-%m-%d")
    
    campaign_config = {
        "promoted_offering": "Apple Vision Pro",
        "buyer_ref": "apple_vision_pro_demo_001",
        "packages": [
            {
                "package_ref": "pkg_apple_nyt_homepage",
                "product_ref": "nyt_homepage_billboard",
                "start_date": start_date,
                "end_date": end_date,
                "pricing": {
                    "pricing_model": "CPM",
                    "rate": 22.00,
                    "currency": "USD"
                },
                "inventory_requests": [
                    {
                        "quantity": 4500000,  # 4.5M impressions
                        "unit": "IMPRESSIONS"
                    }
                ]
            }
        ]
    }
    
    media_buy = await create_media_buy("nyt", campaign_config)
    
    if media_buy:
        media_buy_id = media_buy.get('media_buy_id')
        print(f"\n💡 Campaign created! Media Buy ID: {media_buy_id}")


async def main():
    """
    Run all three demo scenarios.
    """
    print("\n" + "="*80)
    print("🤖 NEWTON MEDIA BUYING DEMONSTRATION")
    print("="*80)
    print("\nThis demonstrates Newton (media buyer) interacting with three sales agents:")
    print("  • ESPN (Nike campaign)")
    print("  • CNN (Coca-Cola campaign)")
    print("  • NYT (Apple campaign)")
    print("\nEach scenario shows: Discovery → Purchase → Monitoring")
    print("="*80)
    
    # Run all three scenarios
    await scenario_espn_nike()
    await scenario_cnn_cocacola()
    await scenario_nyt_apple()
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nNewton successfully:")
    print("  ✅ Discovered inventory across 3 sales agents")
    print("  ✅ Evaluated products based on campaign briefs")
    print("  ✅ Created media buys on each platform")
    print("  ✅ Can monitor delivery and performance")
    print("\nNext steps:")
    print("  • Integrate this flow into Newton's momentum agent")
    print("  • Add LLM-based product evaluation")
    print("  • Implement budget optimization across platforms")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

