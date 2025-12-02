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
            if not currency_limit:
                currency_limit = CurrencyLimit(
                    tenant_id=tenant_id,
                    currency_code="USD",
                    min_package_budget=1000.0,
                    max_daily_package_spend=50000.0,
                )
                session.add(currency_limit)
                print(f"  ✓ Created CurrencyLimit for {tenant_id}")
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

            # Create sample products (different for DSP vs publisher)
            if config.get("tenant_type") == "dsp":
                # DSP products: Audience-focused, programmatic
                # Aligned with Yahoo DSP API terminology (Lines, Exchanges, Deals)
                products_data = [
                    {
                        "name": "Audience-Targeted Display (Open Exchange)",
                        "format": "display_728x90",
                        "description": "Reach high-value audiences across Yahoo Exchange + open web. "
                                       "Supports outdoor_enthusiasts, eco_conscious_consumers, sustainable_shoppers, "
                                       "adventure_travelers audience segments. AUTOBID optimization available.",
                        "pricing_model": "CPM",
                        "rate": 6.50,
                        "is_fixed": False,  # Bid-based (auction)
                        "price_guidance": {"floor": 5.00, "p50": 6.50, "p75": 8.00},
                        "product_suffix": "",  # Use default product_id format
                    },
                    {
                        "name": "Premium Display + Retargeting",
                        "format": "display_300x250",
                        "description": "Medium rectangle with site retargeting pools for abandoned cart recovery. "
                                       "Supports FIRST_PARTY retargeting audiences. Higher CPM for precision targeting.",
                        "pricing_model": "CPM",
                        "rate": 8.00,
                        "is_fixed": False,  # Bid-based (auction)
                        "price_guidance": {"floor": 6.00, "p50": 8.00, "p75": 10.00},
                        "product_suffix": "",
                    },
                    {
                        "name": "Mobile Audience Network",
                        "format": "display_320x50",
                        "description": "Mobile inventory with behavioral targeting across Yahoo mobile properties. "
                                       "Supports fitness_enthusiasts, travel_enthusiasts audience segments.",
                        "pricing_model": "CPM",
                        "rate": 5.50,
                        "is_fixed": False,  # Bid-based (auction)
                        "price_guidance": {"floor": 4.00, "p50": 5.50, "p75": 7.00},
                        "product_suffix": "",
                    },
                    {
                        "name": "Premium PMP Deal - Sports & Outdoor Publishers",
                        "format": "display_300x250",
                        "description": "Private Marketplace (PMP) deal with premium sports and outdoor publishers. "
                                       "PREFERRED_DEAL type with fixed floor price. Higher viewability (75%+) and "
                                       "brand-safe inventory. Ideal for outdoor_enthusiasts, adventure_travelers targeting.",
                        "pricing_model": "CPM",
                        "rate": 12.00,  # Higher CPM for premium PMP inventory
                        "is_fixed": False,  # Still auction-based but with floor
                        "price_guidance": {"floor": 10.00, "p50": 12.00, "p75": 15.00},
                        "product_suffix": "_pmp_sports",  # Special suffix for PMP deal
                    },
                    {
                        "name": "Video Pre-Roll (Programmatic)",
                        "format": "video_30sec",
                        "description": "30-second video pre-roll across Yahoo video network and exchange partners. "
                                       "Supports VIDEO mediaType with video completion tracking. "
                                       "Optimized for VIEWABLE_IMPRESSION goal type.",
                        "pricing_model": "CPM",
                        "rate": 15.00,  # Video typically higher CPM
                        "is_fixed": False,
                        "price_guidance": {"floor": 12.00, "p50": 15.00, "p75": 20.00},
                        "product_suffix": "_video",
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


if __name__ == "__main__":
    create_demo_tenants()
    print("\n✅ All demo tenants initialized!")

