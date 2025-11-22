#!/usr/bin/env python3
"""
Create test principals (advertisers) for each tenant.
Newton will use these principals to authenticate and buy ads.
"""

import secrets
import sys
from sqlalchemy import select

# Add app to path
sys.path.insert(0, '/app')

from src.core.database.database_session import get_db_session
from src.core.database.models import Principal, Tenant

def create_principal(session, tenant_id, principal_id, name):
    """Create a principal with a unique access token."""
    
    # Check if principal already exists
    stmt = select(Principal).filter_by(tenant_id=tenant_id, principal_id=principal_id)
    existing = session.scalars(stmt).first()
    
    if existing:
        print(f"⚠️  Principal '{principal_id}' already exists for tenant '{tenant_id}'")
        print(f"   Access Token: {existing.access_token}")
        return existing.access_token
    
    # Generate secure access token
    access_token = f"adcp_{tenant_id}_{secrets.token_urlsafe(32)}"
    
    # Create principal
    principal = Principal(
        tenant_id=tenant_id,
        principal_id=principal_id,
        name=name,
        platform_mappings={
            "advertiser_id": principal_id,
            "advertiser_name": name
        },
        access_token=access_token
    )
    
    session.add(principal)
    session.commit()
    
    return access_token


def main():
    """Create test principals for ESPN, CNN, and NYT."""
    
    principals_to_create = [
        ("espn", "nike", "Nike Inc."),
        ("cnn", "cocacola", "Coca-Cola"),
        ("nyt", "apple", "Apple Inc."),
    ]
    
    print("Creating test principals (advertisers)...\n")
    
    with get_db_session() as session:
        # Verify tenants exist
        for tenant_id, _, _ in principals_to_create:
            stmt = select(Tenant).filter_by(tenant_id=tenant_id)
            tenant = session.scalars(stmt).first()
            if not tenant:
                print(f"❌ Error: Tenant '{tenant_id}' not found. Please create it first.")
                sys.exit(1)
        
        # Create principals
        tokens = {}
        for tenant_id, principal_id, name in principals_to_create:
            token = create_principal(session, tenant_id, principal_id, name)
            tokens[f"{tenant_id}/{principal_id}"] = token
            print(f"✅ Created principal '{principal_id}' for {tenant_id.upper()}")
            print(f"   Name: {name}")
            print(f"   Access Token: {token}\n")
    
    print("\n" + "="*80)
    print("🎉 All principals created successfully!")
    print("="*80)
    
    print("\n📋 Summary for Newton Integration:\n")
    print("Newton can now connect to these sales agents using the following credentials:\n")
    
    for tenant_id, principal_id, name in principals_to_create:
        token = tokens[f"{tenant_id}/{principal_id}"]
        print(f"**{tenant_id.upper()} Sales Agent:**")
        print(f"  - Publisher: {tenant_id.upper()}")
        print(f"  - Advertiser: {name}")
        print(f"  - MCP URL: http://localhost:9580/mcp/")
        print(f"  - Auth Header: x-adcp-auth: {token}")
        print(f"  - Tenant ID: {tenant_id}")
        print()
    
    print("\n💡 Next Steps:")
    print("1. Configure Newton's MCP client to connect to http://localhost:9580/mcp/")
    print("2. Add authentication headers with the tokens above")
    print("3. Test the connection by calling 'get_products' tool")
    print("4. Create media buys using 'create_media_buy' tool")


if __name__ == "__main__":
    main()

