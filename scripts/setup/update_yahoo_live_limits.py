#!/usr/bin/env python3
"""Quick script to update yahoo_live currency limits for testing."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set DATABASE_URL if not already set (for VPN access)
if not os.environ.get("DATABASE_URL"):
    # You'll need to set this or pass it as an argument
    print("ERROR: DATABASE_URL environment variable not set")
    print("\nUsage:")
    print('  DATABASE_URL="postgresql://user:pass@host:5432/db" python scripts/setup/update_yahoo_live_limits.py')
    sys.exit(1)

from sqlalchemy import select
from src.core.database.database_session import get_db_session
from src.core.database.models import CurrencyLimit


def update_yahoo_live_limits():
    """Update currency limits for yahoo_live tenant to allow small test buys."""
    
    with get_db_session() as session:
        # Find the yahoo_live currency limit
        stmt = select(CurrencyLimit).filter_by(tenant_id="yahoo_live", currency_code="USD")
        currency_limit = session.scalars(stmt).first()
        
        if not currency_limit:
            print("❌ CurrencyLimit for yahoo_live not found!")
            print("   Run init_demo_tenants_aws.py first to create it.")
            return False
        
        # Show current values
        print(f"Current values for yahoo_live:")
        print(f"  min_package_budget: ${currency_limit.min_package_budget}")
        print(f"  max_daily_package_spend: ${currency_limit.max_daily_package_spend}")
        
        # Update to test-friendly values
        currency_limit.min_package_budget = 5.0  # $5 minimum
        currency_limit.max_daily_package_spend = 50.0  # $50 max daily
        
        session.commit()
        
        print(f"\n✅ Updated yahoo_live currency limits:")
        print(f"  min_package_budget: ${currency_limit.min_package_budget}")
        print(f"  max_daily_package_spend: ${currency_limit.max_daily_package_spend}")
        
        return True


if __name__ == "__main__":
    print("🔧 Updating yahoo_live currency limits for testing...\n")
    success = update_yahoo_live_limits()
    if success:
        print("\n🎉 Done! Newton can now create $5 test buys on yahoo_live.")
    else:
        sys.exit(1)

