#!/usr/bin/env python3
"""
Initialize RDS database with demo tenants and products.
Run this from your local machine - it connects to RDS directly.
"""
import os
import sys

# Set database URL for RDS (use the one from terraform.tfvars)
DB_PASSWORD = "SalesAgent2024Demo!"
DB_HOST = "staging-salesagent-db.c96wsm4kko25.us-east-1.rds.amazonaws.com"
os.environ["DATABASE_URL"] = f"postgresql://salesagent:{DB_PASSWORD}@{DB_HOST}:5432/salesagent"
os.environ["PYTHONPATH"] = "/Users/danfinkel/github/opensource/salesagent"

print("=== Initializing RDS Database ===\n")

# Run migrations
print("Step 1: Running Alembic migrations...")
import subprocess
result = subprocess.run(
    ["python", "migrate.py"],
    cwd="/Users/danfinkel/github/opensource/salesagent",
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"❌ Migration failed: {result.stderr}")
    sys.exit(1)

print("\nStep 2: Creating demo tenants (ESPN, CNN, NYT)...")
sys.path.insert(0, "/Users/danfinkel/github/opensource/salesagent")

from scripts.setup.create_test_tenants import create_demo_tenants_and_products

try:
    create_demo_tenants_and_products()
    print("\n✅ Database initialized successfully!")
    print("\nDemo tenants created:")
    print("  - ESPN (tenant_id: espn)")
    print("  - CNN (tenant_id: cnn)")
    print("  - NYT (tenant_id: nyt)")
    print("\nEach tenant has products and is ready for Newton to connect!")
except Exception as e:
    print(f"\n❌ Failed to create demo data: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

