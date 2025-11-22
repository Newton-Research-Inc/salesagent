#!/bin/bash
set -e

echo "🛑 Stopping AdCP Sales Agent Demo Environment"
echo "=============================================="
echo ""

# Change to the salesagent directory
cd "$(dirname "$0")/../.."

# Stop Docker Compose services
echo "📦 Stopping Docker Compose services..."
docker-compose -f docker-compose.testing.yml down

echo ""
echo "✅ All services stopped!"
echo ""
echo "💡 To start again, run:"
echo "   ./scripts/demo/start_demo_agents.sh"

