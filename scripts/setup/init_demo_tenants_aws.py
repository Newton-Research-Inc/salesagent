"""Initialize demo tenants (ESPN, CNN, NYT) for AWS deployment."""
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
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
    """Create ESPN, CNN, NYT tenants if they don't exist."""
    tenants_config = [
        {
            "tenant_id": "espn",
            "name": "ESPN",
            "subdomain": "espn",
            "description": "ESPN Sports Network - Premium sports advertising inventory",
        },
        {
            "tenant_id": "cnn",
            "name": "CNN",
            "subdomain": "cnn",
            "description": "CNN News Network - Premium news advertising inventory",
        },
        {
            "tenant_id": "nyt",
            "name": "New York Times",
            "subdomain": "nyt",
            "description": "New York Times - Premium journalism advertising inventory",
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
                print(f"Tenant {tenant_id} exists - deleting to apply new settings...")
                session.delete(existing)
                session.flush()
                print(f"✓ Deleted existing tenant {tenant_id}")

            print(f"Creating tenant: {tenant_id}...")

            # Create tenant
            tenant = Tenant(
                tenant_id=tenant_id,
                name=config["name"],
                subdomain=config["subdomain"],
                billing_plan="demo",
                ad_server="mock",
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

            # Create currency limit
            currency_limit = CurrencyLimit(
                tenant_id=tenant_id,
                currency_code="USD",
                min_package_budget=1000.0,
                max_daily_package_spend=50000.0,
            )
            session.add(currency_limit)

            # Create property tag
            property_tag = PropertyTag(
                tag_id="all_inventory",
                tenant_id=tenant_id,
                name="All Inventory",
                description="Default tag for all inventory",
                # created_at and updated_at are auto-managed
            )
            session.add(property_tag)

            # Create authorized property
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

            # Create test principal
            principal = Principal(
                principal_id=f"{tenant_id}_test_buyer",
                tenant_id=tenant_id,
                name=f"{config['name']} Test Buyer",
                access_token=f"{tenant_id}-test-token",
                platform_mappings={"mock": {"advertiser_id": f"{tenant_id}-advertiser"}},
            )
            session.add(principal)

            # Create sample products
            products_data = [
                {
                    "name": f"{config['name']} Homepage Banner",
                    "format": "display_728x90",
                    "description": f"Premium leaderboard placement on {config['name']} homepage",
                },
                {
                    "name": f"{config['name']} Sidebar Ad",
                    "format": "display_300x250",
                    "description": f"Medium rectangle on {config['name']} article pages",
                },
                {
                    "name": f"{config['name']} Mobile Banner",
                    "format": "display_320x50",
                    "description": f"Mobile banner on {config['name']} mobile site",
                },
            ]

            for prod_data in products_data:
                product_id = f"{tenant_id}_{prod_data['format']}"
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

                # Add pricing option
                pricing = PricingOption(
                    product_id=product_id,
                    tenant_id=tenant_id,
                    pricing_model="CPM",
                    rate=5.0,
                    currency="USD",
                    is_fixed=True,
                )
                session.add(pricing)

            session.commit()
            print(f"✅ Created tenant {tenant_id} with products and principal")


if __name__ == "__main__":
    create_demo_tenants()
    print("\n✅ All demo tenants initialized!")

