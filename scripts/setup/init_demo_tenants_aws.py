"""Initialize demo tenants (ESPN, CNN, NYT, Yahoo DSP) for AWS deployment."""
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.orm import attributes
from src.core.database.database_session import get_db_session
from src.core.database.models import (
    AuthorizedProperty,
    CurrencyLimit,
    Principal,
    Product,
    PropertyTag,
    Tenant,
    PricingOption,
)


def create_demo_tenants():
    """Create ESPN, CNN, NYT (publisher ad servers) and Yahoo DSP (programmatic) tenants."""
    tenants_config = [
        {
            "tenant_id": "espn",
            "name": "ESPN",
            "subdomain": "espn",
            "description": "ESPN Sports Network - Premium sports advertising inventory",
            "ad_server": "mock",
            "tenant_type": "publisher",
        },
        {
            "tenant_id": "cnn",
            "name": "CNN",
            "subdomain": "cnn",
            "description": "CNN News Network - Premium news advertising inventory",
            "ad_server": "mock",
            "tenant_type": "publisher",
        },
        {
            "tenant_id": "nyt",
            "name": "New York Times",
            "subdomain": "nyt",
            "description": "New York Times - Premium journalism advertising inventory",
            "ad_server": "mock",
            "tenant_type": "publisher",
        },
        {
            "tenant_id": "yahoo",
            "name": "Yahoo DSP",
            "subdomain": "yahoo",
            "description": "Yahoo DSP - Programmatic advertising platform with audience targeting",
            "ad_server": "yahoo_dsp",
            "tenant_type": "dsp",
        },
        {
            "tenant_id": "nbcu",
            "name": "NBCUniversal",
            "subdomain": "nbcu",
            "description": "NBCUniversal - Cross-platform Linear TV + Peacock Streaming advertising",
            "ad_server": "mock",  # NBCU tools handle their own logic
            "tenant_type": "broadcaster",
        },
        {
            "tenant_id": "yahoo_live",
            "name": "Yahoo DSP (Live API)",
            "subdomain": "yahoo-live",
            "description": "Yahoo DSP with REAL API integration - connects to actual Yahoo DSP endpoints",
            "ad_server": "yahoo_dsp_live",  # Uses real Yahoo DSP API
            "tenant_type": "dsp_live",
        },
    ]

    now = datetime.now(UTC)

    with get_db_session() as session:
        for config in tenants_config:
            tenant_id = config["tenant_id"]

            # Check if tenant exists
            stmt = select(Tenant).filter_by(tenant_id=tenant_id)
            existing = session.scalars(stmt).first()

            if existing:
                print(f"Tenant {tenant_id} exists - updating settings...")
                # Update existing tenant with new settings
                existing.name = config["name"]
                existing.subdomain = config["subdomain"]
                existing.billing_plan = "demo"
                existing.ad_server = config.get("ad_server", "mock")
                existing.enable_axe_signals = True
                existing.is_active = True
                existing.authorized_emails = None  # Remove access control
                existing.authorized_domains = None  # Remove access control
                existing.auto_approve_format_ids = ["display_300x250", "display_728x90", "display_320x50"]
                existing.human_review_required = False
                
                # Update policy_settings dict (don't replace - merge)
                if existing.policy_settings is None:
                    existing.policy_settings = {}
                existing.policy_settings["brand_manifest_policy"] = "public"  # Allow public access without auth
                
                # CRITICAL: Mark JSONB fields as modified so SQLAlchemy saves them
                attributes.flag_modified(existing, "policy_settings")
                attributes.flag_modified(existing, "auto_approve_format_ids")
                
                # DEBUG: Log the actual policy_settings dict
                print(f"  DEBUG: policy_settings after update: {existing.policy_settings}")
                
                tenant = existing
                print(f"✓ Updated existing tenant {tenant_id} (ad_server: {existing.ad_server})")
            else:
                print(f"Creating tenant: {tenant_id}...")
                # Create tenant
                tenant = Tenant(
                    tenant_id=tenant_id,
                    name=config["name"],
                    subdomain=config["subdomain"],
                    billing_plan="demo",
                    ad_server=config.get("ad_server", "mock"),
                    enable_axe_signals=True,
                    is_active=True,
                    authorized_emails=None,  # No access control - allow unauthenticated access
                    authorized_domains=None,  # No access control - allow unauthenticated access
                    auto_approve_format_ids=["display_300x250", "display_728x90", "display_320x50"],
                    human_review_required=False,
                    policy_settings={"brand_manifest_policy": "public"},  # Allow public access without auth
                    # created_at and updated_at are auto-managed
                )
                session.add(tenant)

            session.flush()

            # Create or get currency limit
            stmt = select(CurrencyLimit).filter_by(tenant_id=tenant_id, currency_code="USD")
            currency_limit = session.scalars(stmt).first()
            
            # Use lower minimums for yahoo_live tenant (test mode)
            if config.get("tenant_type") == "dsp_live":
                min_budget = 5.0  # $5 minimum for testing
                max_daily = 50.0  # $50 max daily for safety
            else:
                min_budget = 1000.0  # $1,000 for production tenants
                max_daily = 50000.0
                
            if not currency_limit:
                currency_limit = CurrencyLimit(
                    tenant_id=tenant_id,
                    currency_code="USD",
                    min_package_budget=min_budget,
                    max_daily_package_spend=max_daily,
                )
                session.add(currency_limit)
                print(f"  ✓ Created CurrencyLimit for {tenant_id} (min: ${min_budget})")
            else:
                # Update existing currency limit for yahoo_live to use test values
                if config.get("tenant_type") == "dsp_live":
                    currency_limit.min_package_budget = min_budget
                    currency_limit.max_daily_package_spend = max_daily
                    print(f"  ✓ Updated CurrencyLimit for {tenant_id} to test mode (min: ${min_budget})")
                else:
                    print(f"  ℹ️ CurrencyLimit already exists for {tenant_id}")

            # Create or get property tag
            stmt = select(PropertyTag).filter_by(tag_id="all_inventory", tenant_id=tenant_id)
            property_tag = session.scalars(stmt).first()
            if not property_tag:
                property_tag = PropertyTag(
                    tag_id="all_inventory",
                    tenant_id=tenant_id,
                    name="All Inventory",
                    description="Default tag for all inventory",
                    # created_at and updated_at are auto-managed
                )
                session.add(property_tag)
                print(f"  ✓ Created PropertyTag for {tenant_id}")
            else:
                print(f"  ℹ️ PropertyTag already exists for {tenant_id}")

            # Create or get authorized property
            stmt = select(AuthorizedProperty).filter_by(tenant_id=tenant_id, publisher_domain=f"www.{tenant_id}.com")
            auth_prop = session.scalars(stmt).first()
            if not auth_prop:
                auth_prop = AuthorizedProperty(
                    property_id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    property_type="website",
                    name=f"{config['name']} Website",
                    identifiers={"domain": f"www.{tenant_id}.com"},
                    publisher_domain=f"www.{tenant_id}.com",
                    verification_status="verified",
                    # created_at and updated_at are auto-managed
                )
                session.add(auth_prop)
                print(f"  ✓ Created AuthorizedProperty for {tenant_id}")
            else:
                print(f"  ℹ️ AuthorizedProperty already exists for {tenant_id}")

            # Create or get test principal
            stmt = select(Principal).filter_by(principal_id=f"{tenant_id}_test_buyer", tenant_id=tenant_id)
            principal = session.scalars(stmt).first()
            if not principal:
                principal = Principal(
                    principal_id=f"{tenant_id}_test_buyer",
                    tenant_id=tenant_id,
                    name=f"{config['name']} Test Buyer",
                    access_token=f"{tenant_id}-test-token",
                    platform_mappings={"mock": {"advertiser_id": f"{tenant_id}-advertiser"}},
                )
                session.add(principal)
                print(f"  ✓ Created Principal for {tenant_id}")
            else:
                print(f"  ℹ️ Principal already exists for {tenant_id}")

            # For Yahoo DSP, Yahoo DSP Live, and NBCU: Create Honda advertiser principal for demo
            if config.get("tenant_type") in ("dsp", "dsp_live", "broadcaster"):
                stmt = select(Principal).filter_by(principal_id="honda_advertiser", tenant_id=tenant_id)
                honda_principal = session.scalars(stmt).first()
                
                # Determine platform mappings based on adapter type
                if config.get("tenant_type") == "dsp_live":
                    # For live API - credentials will be configured in tenant settings
                    platform_mappings = {
                        "yahoo_dsp_live": {
                            "advertiser_id": "placeholder_advertiser_id",
                            "seat_id": "placeholder_seat_id",
                            "account_name": "Honda Motor Company",
                            "note": "Configure real credentials in tenant settings"
                        }
                    }
                else:
                    # For simulation
                    platform_mappings = {
                        "yahoo_dsp": {
                            "advertiser_id": "12345",
                            "seat_id": "honda_seat_001",
                            "account_name": "Honda Motor Company"
                        }
                    }
                
                if not honda_principal:
                    # Use unique token per tenant to avoid unique constraint violation
                    honda_token = f"honda-demo-token-{tenant_id}"
                    honda_principal = Principal(
                        principal_id="honda_advertiser",
                        tenant_id=tenant_id,
                        name="Honda Motor Company",
                        access_token=honda_token,
                        platform_mappings=platform_mappings,
                    )
                    session.add(honda_principal)
                    print(f"  ✓ Created Honda Principal for {tenant_id} (token: {honda_token})")
                else:
                    print(f"  ℹ️ Honda Principal already exists for {tenant_id}")

            # Create sample products (different for DSP vs publisher vs broadcaster)
            if config.get("tenant_type") == "broadcaster":
                # Broadcaster products: Linear TV + Streaming (NBCU)
                products_data = [
                    {
                        "name": "Sunday Night Football - Linear",
                        "format": "video_30sec",
                        "description": "Premium :30 spot during Sunday Night Football broadcast. "
                                       "P2+ Nielsen-measured audience. Live sports exclusivity with 20-45M viewers per game. "
                                       "Available games: Wildcard, Divisional, Conference championship.",
                        "pricing_model": "CPM",
                        "rate": 21.07,  # SNF CPM
                        "is_fixed": True,
                        "product_suffix": "_snf_linear",
                    },
                    {
                        "name": "Sunday Night Football - Peacock Streaming",
                        "format": "video_30sec",
                        "description": "Premium :30 CTV spot during SNF on Peacock streaming. "
                                       "Non-skippable, 100% completion rate. Captures cord-cutters for incremental reach. "
                                       "Cross-platform measurement available with Linear.",
                        "pricing_model": "CPM",
                        "rate": 33.89,  # Streaming CPM
                        "is_fixed": True,
                        "product_suffix": "_snf_streaming",
                    },
                    {
                        "name": "NBA Primetime - Linear",
                        "format": "video_30sec",
                        "description": "Premium :30 spot during NBA primetime broadcasts. "
                                       "Includes Christmas Day games and regular season primetime. "
                                       "P2+ Nielsen-measured audience.",
                        "pricing_model": "CPM",
                        "rate": 19.47,
                        "is_fixed": True,
                        "product_suffix": "_nba_linear",
                    },
                    {
                        "name": "NBA - Peacock Streaming",
                        "format": "video_30sec",
                        "description": "Premium :30 CTV spot during NBA on Peacock streaming. "
                                       "Non-skippable with completion tracking.",
                        "pricing_model": "CPM",
                        "rate": 33.89,
                        "is_fixed": True,
                        "product_suffix": "_nba_streaming",
                    },
                    {
                        "name": "Entertainment - Golden Globes",
                        "format": "video_30sec",
                        "description": "Premium :30 spot during Golden Globes broadcast. "
                                       "High-profile awards show with affluent audience.",
                        "pricing_model": "CPM",
                        "rate": 23.61,
                        "is_fixed": True,
                        "product_suffix": "_awards_linear",
                    },
                ]
            elif config.get("tenant_type") in ("dsp", "dsp_live"):
                # DSP products: Audience-focused, programmatic
                # Aligned with Yahoo DSP API terminology (Lines, Exchanges, Deals)
                # AUTOMOTIVE-FOCUSED for Honda demo
                products_data = [
                    {
                        "name": "Audience-Targeted Display",
                        "format": "display_300x250",
                        "description": "Programmatic display with advanced audience targeting across Yahoo Exchange and open web. "
                                       "Supports INTEREST, FACT, LOOKALIKE, and CONVERSIONRULE segment types. "
                                       "Auto intender segments available (SUV, Crossover, In-Market). "
                                       "AUTOBID optimization with learning phase support. "
                                       "Use getAudienceSegments to discover available segments.",
                        "pricing_model": "CPM",
                        "rate": 8.00,
                        "is_fixed": False,  # Bid-based (auction)
                        "price_guidance": {"floor": 6.00, "p50": 8.00, "p75": 10.00},
                        "product_suffix": "",
                    },
                    {
                        "name": "Premium PMP Deal - Automotive Publishers",
                        "format": "display_300x250",
                        "description": "Private Marketplace (PMP) deal with premium automotive publishers (KBB, Edmunds, Cars.com, MotorTrend). "
                                       "PREFERRED_DEAL type with fixed floor price. "
                                       "Higher viewability (75%+) and brand-safe inventory. "
                                       "Ideal for auto intender and competitive conquest targeting.",
                        "pricing_model": "CPM",
                        "rate": 12.00,  # Higher CPM for premium PMP inventory
                        "is_fixed": False,  # Still auction-based but with floor
                        "price_guidance": {"floor": 10.00, "p50": 12.00, "p75": 15.00},
                        "product_suffix": "_pmp_auto",  # Special suffix for automotive PMP deal
                    },
                    {
                        "name": "Mobile Audience Network",
                        "format": "display_320x50",
                        "description": "Mobile inventory with behavioral targeting across Yahoo mobile properties. "
                                       "Strong performance for auto intenders on mobile devices. "
                                       "Supports location-based targeting near dealerships.",
                        "pricing_model": "CPM",
                        "rate": 5.50,
                        "is_fixed": False,  # Bid-based (auction)
                        "price_guidance": {"floor": 4.00, "p50": 5.50, "p75": 7.00},
                        "product_suffix": "_mobile",
                    },
                    {
                        "name": "Retargeting Display",
                        "format": "display_300x250",
                        "description": "Site retargeting for users who visited advertiser websites. "
                                       "Supports CONVERSIONRULE segments (page visitors, build & price abandoners, dealer locator users). "
                                       "Highest conversion rates at efficient CPMs.",
                        "pricing_model": "CPM",
                        "rate": 5.00,
                        "is_fixed": False,
                        "price_guidance": {"floor": 4.00, "p50": 5.00, "p75": 6.00},
                        "product_suffix": "_retarget",
                    },
                    {
                        "name": "Video Pre-Roll (Programmatic)",
                        "format": "video_30sec",
                        "description": "30-second video pre-roll across Yahoo video network and exchange partners. "
                                       "Supports VIDEO mediaType with video completion tracking. "
                                       "Strong brand impact for automotive launches.",
                        "pricing_model": "CPM",
                        "rate": 15.00,  # Video typically higher CPM
                        "is_fixed": False,
                        "price_guidance": {"floor": 12.00, "p50": 15.00, "p75": 20.00},
                        "product_suffix": "_video",
                    },
                    {
                        "name": "Leaderboard Display",
                        "format": "display_728x90",
                        "description": "Leaderboard display with audience targeting across Yahoo Exchange + open web. "
                                       "Good for brand awareness campaigns with broad reach. "
                                       "Supports all segment types.",
                        "pricing_model": "CPM",
                        "rate": 6.50,
                        "is_fixed": False,
                        "price_guidance": {"floor": 5.00, "p50": 6.50, "p75": 8.00},
                        "product_suffix": "",
                    },
                ]
            else:
                # Publisher products: Placement-focused, guaranteed
                products_data = [
                    {
                        "name": f"{config['name']} Homepage Banner",
                        "format": "display_728x90",
                        "description": f"Premium leaderboard placement on {config['name']} homepage",
                        "pricing_model": "CPM",
                        "rate": 5.0,
                        "is_fixed": True,  # Fixed rate for publisher direct
                    },
                    {
                        "name": f"{config['name']} Sidebar Ad",
                        "format": "display_300x250",
                        "description": f"Medium rectangle on {config['name']} article pages",
                        "pricing_model": "CPM",
                        "rate": 5.0,
                        "is_fixed": True,
                    },
                    {
                        "name": f"{config['name']} Mobile Banner",
                        "format": "display_320x50",
                        "description": f"Mobile banner on {config['name']} mobile site",
                        "pricing_model": "CPM",
                        "rate": 5.0,
                        "is_fixed": True,
                    },
                ]

            for prod_data in products_data:
                # Generate product_id - use custom suffix if provided, otherwise use format
                suffix = prod_data.get("product_suffix", "")
                if suffix:
                    product_id = f"{tenant_id}_{prod_data['format']}{suffix}"
                else:
                    product_id = f"{tenant_id}_{prod_data['format']}"
                
                # Check if product already exists
                stmt = select(Product).filter_by(product_id=product_id, tenant_id=tenant_id)
                product = session.scalars(stmt).first()
                
                if not product:
                    product = Product(
                        product_id=product_id,
                        tenant_id=tenant_id,
                        name=prod_data["name"],
                        description=prod_data["description"],
                        format_ids=[{
                            "agent_url": "https://creatives.adcontextprotocol.org",
                            "id": prod_data["format"]
                        }],
                        property_tags=["all_inventory"],
                        targeting_template={},
                        delivery_type="guaranteed",
                        # created_at and updated_at are auto-managed by SQLAlchemy
                    )
                    session.add(product)
                    session.flush()
                    print(f"  ✓ Created Product: {product_id}")
                else:
                    print(f"  ℹ️ Product already exists: {product_id}")

                # Check if pricing option already exists
                stmt = select(PricingOption).filter_by(product_id=product_id, tenant_id=tenant_id, pricing_model=prod_data.get("pricing_model", "CPM"))
                pricing = session.scalars(stmt).first()
                
                if not pricing:
                    pricing = PricingOption(
                        product_id=product_id,
                        tenant_id=tenant_id,
                        pricing_model=prod_data.get("pricing_model", "CPM"),
                        rate=prod_data.get("rate", 5.0),
                        currency="USD",
                        is_fixed=prod_data.get("is_fixed", True),
                        price_guidance=prod_data.get("price_guidance"),  # Include price guidance for auction pricing
                    )
                    session.add(pricing)
                    print(f"  ✓ Created PricingOption for {product_id}")
                else:
                    print(f"  ℹ️ PricingOption already exists for {product_id}")

            session.commit()
            print(f"✅ Created tenant {tenant_id} with products and principal")


def populate_ctv_formats():
    """Ensure CTV video formats exist in the database."""
    from scripts.setup.populate_creative_formats import CTV_VIDEO_FORMATS
    from src.core.database.models import CreativeFormat
    import json
    
    with get_db_session() as session:
        for fmt in CTV_VIDEO_FORMATS:
            stmt = select(CreativeFormat).filter_by(format_id=fmt["format_id"])
            existing = session.scalars(stmt).first()
            
            if existing:
                print(f"  ℹ️ CTV format {fmt['format_id']} already exists")
                continue
            
            new_format = CreativeFormat(
                format_id=fmt["format_id"],
                name=fmt["name"],
                type=fmt["type"],
                description=fmt["description"],
                width=fmt.get("width"),
                height=fmt.get("height"),
                duration_seconds=fmt.get("duration_seconds"),
                max_file_size_kb=fmt.get("max_file_size_kb"),
                specs=json.dumps(fmt["specs"]),
                is_standard=True,
            )
            session.add(new_format)
            print(f"  ✓ Added CTV format: {fmt['name']}")
        
        session.commit()
    print("✅ CTV video formats populated!")


if __name__ == "__main__":
    create_demo_tenants()
    print("\n📺 Populating CTV video formats...")
    populate_ctv_formats()
    print("\n✅ All demo tenants initialized!")

