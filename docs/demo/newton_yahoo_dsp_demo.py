#!/usr/bin/env python3
"""
Newton Yahoo DSP Demo Script

Demonstrates Newton making strategic decisions across direct (ESPN) 
and programmatic (Yahoo DSP) channels.

Usage:
    python docs/demo/newton_yahoo_dsp_demo.py
"""

import json
from datetime import datetime, timedelta

# Simulated MCP client calls
# In production, these would be actual MCP tool calls

def demo_scenario_1_discovery():
    """Act 1: Newton discovers inventory options."""
    print("\n" + "="*70)
    print("ACT 1: DISCOVERY - Newton Explores Inventory Options")
    print("="*70)
    
    print("\n🤖 Newton: 'I need to find the best inventory for Nike Air Jordan launch.'")
    print("           'Let me check both direct publisher (ESPN) and programmatic (Yahoo DSP)...'\n")
    
    # ESPN discovery
    print("📞 Calling: mcp_espn.get_products()")
    espn_products = {
        "products": [{
            "product_id": "espn_display_728x90",
            "name": "ESPN Homepage Banner",
            "pricing_options": [{
                "pricing_model": "CPM",
                "rate": 5.00,
                "is_fixed": True
            }],
            "delivery_type": "guaranteed"
        }]
    }
    print(f"✅ ESPN Response: {json.dumps(espn_products, indent=2)}")
    
    # Yahoo DSP discovery
    print("\n📞 Calling: mcp_yahoo.get_products()")
    yahoo_products = {
        "products": [{
            "product_id": "yahoo_display_728x90",
            "name": "Audience-Targeted Display",
            "pricing_options": [{
                "pricing_model": "CPM",
                "rate": 6.50,
                "is_fixed": False,
                "price_guidance": {
                    "floor": 5.00,
                    "p50": 6.50,
                    "p75": 8.00
                }
            }],
            "targeting_template": {
                "audiences_any_of": ["auto_intenders", "fitness_enthusiasts"]
            },
            "delivery_type": "programmatic"
        }]
    }
    print(f"✅ Yahoo DSP Response: {json.dumps(yahoo_products, indent=2)}")
    
    # Newton's analysis
    print("\n🧠 Newton's Analysis:")
    print("   ESPN:")
    print("   ✅ Lower CPM ($5.00 fixed)")
    print("   ✅ Guaranteed delivery")
    print("   ❌ No audience targeting (reaches ALL ESPN visitors)")
    print("")
    print("   Yahoo DSP:")
    print("   ✅ Audience targeting (auto_intenders + fitness_enthusiasts)")
    print("   ✅ Broader reach (100+ sites)")
    print("   ❌ Higher CPM ($6.50, +30%)")
    print("   ❌ Non-guaranteed delivery")
    print("")
    print("   💡 DECISION: Split budget - $25K ESPN + $25K Yahoo DSP")
    print("   📊 RATIONALE: Diversification + test audience targeting value")


def demo_scenario_2_execution():
    """Act 2: Newton executes buys on both platforms."""
    print("\n" + "="*70)
    print("ACT 2: EXECUTION - Newton Places Orders")
    print("="*70)
    
    # ESPN execution
    print("\n🎯 ESPN Buy (Direct/Simple):")
    print("📞 Calling: mcp_espn.create_media_buy()")
    print("   Budget: $25,000")
    print("   Impressions: 5,000,000 (at $5.00 CPM)")
    print("   Targeting: ESPN Homepage (placement-based)")
    
    espn_response = {
        "status": "active",  # Immediate
        "media_buy_id": "mock_espn_12345",
        "packages": [{
            "status": "delivering"
        }]
    }
    print(f"✅ ESPN Response: {json.dumps(espn_response, indent=2)}")
    print("   🟢 Campaign activated IMMEDIATELY")
    
    # Yahoo DSP execution
    print("\n🎯 Yahoo DSP Buy (Programmatic/Complex):")
    print("📞 Calling: mcp_yahoo.create_media_buy()")
    print("   Budget: $25,000")
    print("   Targeting: auto_intenders + fitness_enthusiasts + high_income")
    
    yahoo_response = {
        "status": "pending_review",  # Requires approval
        "media_buy_id": "yahoo_dsp_abc123",
        "bid_landscape": {
            "median_winning_bid": 6.83,
            "competition_level": "medium",
            "estimated_win_rate_at_bid": {
                "6.50": 0.45
            }
        },
        "estimated_reach": {
            "estimated_unique_users": 2500000,
            "estimated_impressions": 3846154
        }
    }
    print(f"✅ Yahoo DSP Response: {json.dumps(yahoo_response, indent=2)}")
    print("   🟡 Campaign PENDING REVIEW (DSP approval process)")
    print("   📊 Estimated reach: 2.5M users, 3.8M impressions")
    print("   📊 Win rate at $6.50 bid: 45%")


def demo_scenario_3_performance():
    """Act 3: Newton analyzes performance after 1 week."""
    print("\n" + "="*70)
    print("ACT 3: PERFORMANCE ANALYSIS - Week 1 Results")
    print("="*70)
    
    print("\n⏰ One week later...")
    print("🤖 Newton: 'Let me check how both campaigns are performing...'\n")
    
    # ESPN performance
    print("📞 Calling: mcp_espn.get_media_buy_delivery()")
    espn_performance = {
        "packages": [{
            "impressions": 1250000,
            "spend": 6250.00,
            "avg_cpm": 5.00
        }]
    }
    print(f"✅ ESPN Performance: {json.dumps(espn_performance, indent=2)}")
    print("   📊 Basic metrics only (no click/conversion data)")
    
    # Yahoo DSP performance
    print("\n📞 Calling: mcp_yahoo.get_media_buy_delivery()")
    yahoo_performance = {
        "packages": [{
            "impressions": 962500,
            "clicks": 1060,
            "spend": 6256.25,
            "avg_cpm": 6.51,
            "metadata": {
                "bid_requests": 3125000,
                "win_rate": 0.308,
                "viewability_rate": 0.74,
                "ctr": 0.0011,
                "conversions": 24,
                "conversion_rate": 0.0226
            }
        }]
    }
    print(f"✅ Yahoo DSP Performance: {json.dumps(yahoo_performance, indent=2)}")
    print("   📊 Rich metrics: clicks, conversions, win rate, viewability!")
    
    # Newton's deep analysis
    print("\n🧠 Newton's Performance Analysis:")
    print("\n   REACH COMPARISON:")
    print("   • ESPN: 1.25M impressions (broader, less targeted)")
    print("   • Yahoo DSP: 963K impressions (fewer, but more relevant)")
    print("")
    print("   EFFICIENCY COMPARISON:")
    print("   • ESPN: Unknown clicks/conversions ❌")
    print("   • Yahoo DSP:")
    print("     - 1,060 clicks (0.11% CTR) ✅")
    print("     - 24 conversions (2.26% conversion rate) ✅")
    print("     - 74% viewability (high quality) ✅")
    print("     - Won 30.8% of 3.1M auctions ✅")
    print("")
    print("   COST ANALYSIS:")
    print("   • ESPN: $5.00 CPM (cost per impression)")
    print("   • Yahoo DSP: $6.51 CPM, BUT...")
    print("     - Cost per click: $5.90")
    print("     - Cost per conversion: $260.68")
    print("")
    print("   💡 KEY INSIGHT:")
    print("   Yahoo DSP's 30% higher CPM is justified by:")
    print("   1. Audience targeting → Better conversion rate (2.26%)")
    print("   2. Performance tracking → Can optimize")
    print("   3. Viewability data → Higher quality (74%)")


def demo_scenario_4_optimization():
    """Act 4: Newton makes strategic recommendations."""
    print("\n" + "="*70)
    print("ACT 4: OPTIMIZATION - Newton's Strategic Recommendation")
    print("="*70)
    
    print("\n🤖 Newton: 'Based on Week 1 data, here's my recommendation...'\n")
    
    print("📊 STRATEGIC REPORT:")
    print("")
    print("   Current Allocation: 50/50 ($25K ESPN + $25K Yahoo DSP)")
    print("")
    print("   Week 1 Results:")
    print("   • ESPN: 1.25M impressions, $6,250 spend")
    print("     - Metrics: Basic only")
    print("     - Conversion tracking: None")
    print("")
    print("   • Yahoo DSP: 963K impressions, $6,256 spend")
    print("     - Clicks: 1,060 (measurable!)")
    print("     - Conversions: 24 (measurable!)")
    print("     - Cost per conversion: $260.68")
    print("")
    print("   🎯 RECOMMENDATION: Shift budget 70/30 to Yahoo DSP")
    print("")
    print("   REASONING:")
    print("   1. Yahoo DSP provides measurable conversions")
    print("   2. Can optimize based on performance data")
    print("   3. Audience targeting proving effective (2.26% conv rate)")
    print("   4. ESPN lacks conversion tracking (can't measure ROI)")
    print("")
    print("   📈 EXPECTED OUTCOMES (Weeks 2-4):")
    print("   • Yahoo DSP: 70% budget → ~72 conversions (vs 24 in Week 1)")
    print("   • ESPN: 30% budget → Maintain awareness/reach")
    print("   • Total: Better ROI + ability to prove performance")
    print("")
    print("   ⚠️  CAVEAT:")
    print("   Install Nike conversion pixel for ESPN to compare apples-to-apples")
    print("   Re-evaluate in Week 3 with complete data from both channels")


def demo_comparison_chart():
    """Visual comparison of ESPN vs Yahoo DSP."""
    print("\n" + "="*70)
    print("FINAL COMPARISON: ESPN (Direct) vs Yahoo DSP (Programmatic)")
    print("="*70)
    
    comparison = """
    
    ┌─────────────────────────┬─────────────────┬─────────────────────┐
    │ Feature                 │ ESPN (Direct)   │ Yahoo DSP (Prog.)   │
    ├─────────────────────────┼─────────────────┼─────────────────────┤
    │ CPM                     │ $5.00 (fixed)   │ $6.51 (auction)     │
    │ Delivery                │ Guaranteed      │ Non-guaranteed      │
    │ Activation              │ Immediate       │ Requires approval   │
    │ Targeting               │ Placement       │ Audience segments   │
    │ Click tracking          │ ❌ No           │ ✅ Yes (1,060)      │
    │ Conversion tracking     │ ❌ No           │ ✅ Yes (24)         │
    │ Viewability             │ ❌ Unknown      │ ✅ 74%              │
    │ Win rate data           │ ❌ N/A          │ ✅ 30.8%            │
    │ Optimization potential  │ ⭐ Low          │ ⭐⭐⭐ High          │
    │ Cost per conversion     │ ❓ Unknown      │ ✅ $260.68          │
    └─────────────────────────┴─────────────────┴─────────────────────┘
    
    💡 KEY TAKEAWAY:
    ESPN is simpler and cheaper per impression, but Yahoo DSP provides 
    the data needed to optimize and prove ROI. For performance marketing,
    Yahoo DSP's audience targeting and measurement justify the higher CPM.
    """
    print(comparison)


def main():
    """Run the full demo."""
    print("\n" + "="*70)
    print("🎬 NEWTON + YAHOO DSP DEMO")
    print("="*70)
    print("\n📋 Scenario: Nike Air Jordan Launch Campaign")
    print("💰 Budget: $50,000")
    print("🎯 Goal: Reach sneaker enthusiasts with measurable results")
    print("\n🤖 Newton will:")
    print("   1. Discover options (ESPN vs Yahoo DSP)")
    print("   2. Execute strategic buy (split budget)")
    print("   3. Analyze performance (Week 1)")
    print("   4. Optimize allocation (data-driven)")
    
    input("\n▶️  Press Enter to start demo...")
    
    # Run each act
    demo_scenario_1_discovery()
    input("\n▶️  Press Enter to continue to Act 2...")
    
    demo_scenario_2_execution()
    input("\n▶️  Press Enter to continue to Act 3...")
    
    demo_scenario_3_performance()
    input("\n▶️  Press Enter to continue to Act 4...")
    
    demo_scenario_4_optimization()
    input("\n▶️  Press Enter for final comparison...")
    
    demo_comparison_chart()
    
    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    print("\n🎯 What Newton Demonstrated:")
    print("   ✅ Multi-channel discovery (ESPN + Yahoo DSP)")
    print("   ✅ Strategic decision-making (split budget)")
    print("   ✅ Data-driven optimization (shift to Yahoo DSP)")
    print("   ✅ Understanding trade-offs (guaranteed vs targeted)")
    print("")
    print("🚀 What Yahoo DSP Enables:")
    print("   ✅ Audience targeting (fitness enthusiasts, auto-intenders)")
    print("   ✅ Performance measurement (clicks, conversions, viewability)")
    print("   ✅ Optimization potential (bid adjustments, budget shifts)")
    print("   ✅ Transparent pricing (bid landscape, win rates)")
    print("")
    print("💡 Key Insight:")
    print("   AdCP protocol makes direct (ESPN) and programmatic (Yahoo DSP)")
    print("   look the same to Newton - same tools, different capabilities!")
    print("")


if __name__ == "__main__":
    main()

