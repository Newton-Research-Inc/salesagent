#!/bin/bash
# Clean up all media buys from demo tenants
# Usage: ./scripts/demo/clean_campaigns.sh

set -e

echo "🧹 Cleaning up media buys for demo tenants..."

# Delete media buys and packages for ESPN, CNN, NYT
docker-compose -f docker-compose.testing.yml exec -T postgres psql -U adcp_user -d adcp << 'EOFPG'
-- Delete packages first (foreign key constraint)
DELETE FROM media_packages 
WHERE media_buy_id IN (
    SELECT media_buy_id 
    FROM media_buys 
    WHERE tenant_id IN ('espn', 'cnn', 'nyt')
);

-- Delete media buys
DELETE FROM media_buys 
WHERE tenant_id IN ('espn', 'cnn', 'nyt');

-- Show summary
SELECT 
    'Campaigns cleaned' as status,
    (SELECT COUNT(*) FROM media_buys) as total_remaining_campaigns;
EOFPG

echo "✅ Cleanup complete!"

