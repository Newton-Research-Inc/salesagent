"""Update Yahoo tenant to use yahoo_dsp adapter."""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from src.core.database.database_session import get_db_session
from src.core.database.models import Tenant


def update_yahoo_tenant():
    """Update the yahoo tenant to use yahoo_dsp adapter."""
    with get_db_session() as session:
        stmt = select(Tenant).filter_by(tenant_id="yahoo")
        tenant = session.scalars(stmt).first()
        
        if not tenant:
            print("❌ Yahoo tenant not found!")
            return False
        
        print(f"Current adapter: {tenant.ad_server}")
        
        if tenant.ad_server != "yahoo_dsp":
            tenant.ad_server = "yahoo_dsp"
            session.commit()
            print("✅ Updated yahoo tenant to use yahoo_dsp adapter!")
        else:
            print("ℹ️ Yahoo tenant already using yahoo_dsp adapter")
        
        return True


if __name__ == "__main__":
    success = update_yahoo_tenant()
    sys.exit(0 if success else 1)

