#!/usr/bin/env python3
"""
Populate ESPN, CNN, and NYT tenants with realistic advertising products.
Creates a demo scenario for Newton (media buyer) to discover and purchase inventory.
"""

import sys
from datetime import UTC, datetime

sys.path.insert(0, '/app')

from sqlalchemy import select
from src.core.database.database_session import get_db_session
from src.core.database.models import Product, PropertyTag, Tenant


def create_property_tags(session, tenant_id, tags_data):
    """Create property tags for a tenant."""
    for tag_data in tags_data:
        # Check if tag exists
        stmt = select(PropertyTag).filter_by(tenant_id=tenant_id, tag_id=tag_data['tag_id'])
        existing = session.scalars(stmt).first()
        
        if not existing:
            tag = PropertyTag(
                tenant_id=tenant_id,
                tag_id=tag_data['tag_id'],
                name=tag_data['name'],
                description=tag_data['description']
            )
            session.add(tag)
            print(f"  ✅ Created property tag: {tag_data['name']}")
        else:
            print(f"  ⚠️  Property tag already exists: {tag_data['name']}")


def create_products(session, tenant_id, products_data):
    """Create products for a tenant."""
    for prod_data in products_data:
        # Check if product exists
        stmt = select(Product).filter_by(tenant_id=tenant_id, product_id=prod_data['product_id'])
        existing = session.scalars(stmt).first()
        
        if existing:
            print(f"  ⚠️  Product already exists: {prod_data['name']}")
            continue
        
        product = Product(
            tenant_id=tenant_id,
            product_id=prod_data['product_id'],
            name=prod_data['name'],
            description=prod_data['description'],
            formats=prod_data['formats'],
            targeting_template=prod_data['targeting_template'],
            delivery_type=prod_data.get('delivery_type', 'guaranteed'),
            property_tags=prod_data.get('property_tags', ['all_inventory']),
            implementation_config=prod_data.get('implementation_config'),
            countries=prod_data.get('countries', ['US'])
        )
        session.add(product)
        print(f"  ✅ Created product: {prod_data['name']}")


def main():
    """Populate demo products for ESPN, CNN, and NYT."""
    
    print("🏢 Populating demo products for Newton integration...\n")
    
    with get_db_session() as session:
        # Verify tenants exist
        for tenant_id in ['espn', 'cnn', 'nyt']:
            stmt = select(Tenant).filter_by(tenant_id=tenant_id)
            tenant = session.scalars(stmt).first()
            if not tenant:
                print(f"❌ Error: Tenant '{tenant_id}' not found. Please create it first.")
                sys.exit(1)
        
        # =========================================
        # ESPN - Sports Inventory
        # =========================================
        print("🏈 ESPN - Sports Inventory\n")
        
        espn_property_tags = [
            {
                'tag_id': 'all_inventory',
                'name': 'All ESPN Inventory',
                'description': 'All available ESPN advertising inventory'
            },
            {
                'tag_id': 'premium_sports',
                'name': 'Premium Sports Pages',
                'description': 'High-traffic pages: NFL, NBA, MLB, Soccer'
            },
            {
                'tag_id': 'live_games',
                'name': 'Live Game Coverage',
                'description': 'Live game pages and scores'
            }
        ]
        
        espn_products = [
            {
                'product_id': 'espn_homepage_leaderboard',
                'name': 'ESPN Homepage - Leaderboard',
                'description': 'Premium leaderboard placement on ESPN.com homepage. High visibility, sports enthusiast audience.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_728x90'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['sports', 'football', 'basketball']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory', 'premium_sports'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 8.0,
                    'recommended_cpm': 12.0,
                    'estimated_daily_impressions': 1000000
                }
            },
            {
                'product_id': 'espn_live_game_sidebar',
                'name': 'Live Game Sidebar - Rectangle',
                'description': 'Sidebar placement on live game pages. Highly engaged audience during games.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_300x250'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['sports', 'live_events']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['live_games'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 10.0,
                    'recommended_cpm': 15.0,
                    'estimated_daily_impressions': 500000
                }
            },
            {
                'product_id': 'espn_mobile_banner',
                'name': 'ESPN Mobile App - Banner',
                'description': 'Mobile app banner placement. Reaches ESPN mobile app users.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_320x50'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'device_type_any_of': ['mobile']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 5.0,
                    'recommended_cpm': 7.0,
                    'estimated_daily_impressions': 2000000
                }
            }
        ]
        
        create_property_tags(session, 'espn', espn_property_tags)
        create_products(session, 'espn', espn_products)
        session.commit()
        print()
        
        # =========================================
        # CNN - News Inventory
        # =========================================
        print("📰 CNN - News Inventory\n")
        
        cnn_property_tags = [
            {
                'tag_id': 'all_inventory',
                'name': 'All CNN Inventory',
                'description': 'All available CNN advertising inventory'
            },
            {
                'tag_id': 'breaking_news',
                'name': 'Breaking News',
                'description': 'High-impact breaking news pages'
            },
            {
                'tag_id': 'politics',
                'name': 'Politics Section',
                'description': 'Political news and analysis'
            }
        ]
        
        cnn_products = [
            {
                'product_id': 'cnn_homepage_leaderboard',
                'name': 'CNN Homepage - Leaderboard',
                'description': 'Premium leaderboard on CNN.com homepage. News-focused, educated audience.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_728x90'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['news', 'politics', 'current_events']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 10.0,
                    'recommended_cpm': 15.0,
                    'estimated_daily_impressions': 1500000
                }
            },
            {
                'product_id': 'cnn_article_skyscraper',
                'name': 'Article Sidebar - Wide Skyscraper',
                'description': 'Sidebar placement on article pages. Long dwell time, engaged readers.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_160x600'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['news', 'reading']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 7.0,
                    'recommended_cpm': 10.0,
                    'estimated_daily_impressions': 800000
                }
            },
            {
                'product_id': 'cnn_breaking_news_banner',
                'name': 'Breaking News Alert - Banner',
                'description': 'Banner on breaking news alerts. High visibility during major events.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_970x250'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['news', 'breaking_news']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['breaking_news'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 12.0,
                    'recommended_cpm': 18.0,
                    'estimated_daily_impressions': 400000
                }
            }
        ]
        
        create_property_tags(session, 'cnn', cnn_property_tags)
        create_products(session, 'cnn', cnn_products)
        session.commit()
        print()
        
        # =========================================
        # NYT - Premium News Inventory
        # =========================================
        print("📖 New York Times - Premium Inventory\n")
        
        nyt_property_tags = [
            {
                'tag_id': 'all_inventory',
                'name': 'All NYT Inventory',
                'description': 'All available New York Times advertising inventory'
            },
            {
                'tag_id': 'premium_content',
                'name': 'Premium Content',
                'description': 'High-quality journalism and in-depth reporting'
            },
            {
                'tag_id': 'opinion',
                'name': 'Opinion Section',
                'description': 'Opinion and editorial content'
            }
        ]
        
        nyt_products = [
            {
                'product_id': 'nyt_homepage_billboard',
                'name': 'NYT Homepage - Billboard',
                'description': 'Premium billboard placement on NYTimes.com homepage. Affluent, educated audience.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_970x250'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['news', 'premium_content', 'culture']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory', 'premium_content'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 15.0,
                    'recommended_cpm': 22.0,
                    'estimated_daily_impressions': 800000
                }
            },
            {
                'product_id': 'nyt_article_rectangle',
                'name': 'Article Inline - Rectangle',
                'description': 'Inline placement within articles. High engagement, long-form readers.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_300x250'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['news', 'reading', 'journalism']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['all_inventory'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 12.0,
                    'recommended_cpm': 18.0,
                    'estimated_daily_impressions': 600000
                }
            },
            {
                'product_id': 'nyt_opinion_leaderboard',
                'name': 'Opinion Section - Leaderboard',
                'description': 'Leaderboard in opinion/editorial section. Highly engaged political audience.',
                'formats': [
                    {
                        'agent_url': 'http://localhost:9580/mcp/',
                        'id': 'display_728x90'
                    }
                ],
                'targeting_template': {
                    'targeting': {
                        'geo_country_any_of': ['US'],
                        'interests_any_of': ['politics', 'opinion', 'current_events']
                    }
                },
                'delivery_type': 'guaranteed',
                'property_tags': ['opinion'],
                'countries': ['US'],
                'implementation_config': {
                    'floor_cpm': 10.0,
                    'recommended_cpm': 14.0,
                    'estimated_daily_impressions': 300000
                }
            }
        ]
        
        create_property_tags(session, 'nyt', nyt_property_tags)
        create_products(session, 'nyt', nyt_products)
        session.commit()
        print()
        
    print("=" * 80)
    print("🎉 Demo products created successfully!")
    print("=" * 80)
    print()
    print("📊 Summary:")
    print("  • ESPN: 3 products (sports-focused inventory)")
    print("  • CNN: 3 products (news-focused inventory)")
    print("  • NYT: 3 products (premium news inventory)")
    print()
    print("💡 Newton can now discover these products using:")
    print("   tool: get_products")
    print("   brief: 'Show me premium display inventory for a sports brand'")
    print()


if __name__ == "__main__":
    main()

