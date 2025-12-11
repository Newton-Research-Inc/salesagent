"""
NBCU MCP Tools - Linear & Streaming Ad Sales

Tools for NBCU's cross-platform advertising workflow:
- getProducts: Get available inventory for Linear & Streaming
- getMeasurement: Calculate cross-platform reach/frequency estimates
- savePlan: Book a plan and get confirmation

Based on NBCU's MCP API specification.
"""

import logging
import random
import uuid
from datetime import datetime, UTC
from typing import Any, ClassVar

from fastmcp import Context
from fastmcp.tools import ToolResult

logger = logging.getLogger(__name__)


# ============================================================================
# NBCU Simulated Data Store
# ============================================================================

class NBCUDataStore:
    """Simulated NBCU inventory and plans database."""
    
    # Class-level storage to persist across requests
    saved_plans: ClassVar[dict[str, Any]] = {}
    plan_counter: ClassVar[int] = 100
    
    # SNF (Sunday Night Football) Q1 2026 inventory
    SNF_INVENTORY: ClassVar[list[dict[str, Any]]] = [
        {
            "salesUnitId": 786362,
            "name": "NFL Game 20 Live TBD vs TBD - 01/04/26",
            "weekOfDate": "2025-12-29",
            "unitPrice": 443171,
            "impressions": 21033000,
            "CPM": 21.07,
            "avails": 19.5,
            "division": "SPORTS",
            "subDivision": "SNF",
        },
        {
            "salesUnitId": 786366,
            "name": "NFL Game 21 Live - WILDCARD 01/11/26",
            "weekOfDate": "2026-01-05",
            "unitPrice": 658952,
            "impressions": 31274000,
            "CPM": 21.07,
            "avails": 0.5,
            "division": "SPORTS",
            "subDivision": "SNF",
        },
        {
            "salesUnitId": 786370,
            "name": "NFL Game 22 Live - DIVISIONAL 01/18/26",
            "weekOfDate": "2026-01-12",
            "unitPrice": 803620,
            "impressions": 38140000,
            "CPM": 21.07,
            "avails": 3.5,
            "division": "SPORTS",
            "subDivision": "SNF",
        },
        {
            "salesUnitId": 786374,
            "name": "NFL Game 23 Live - CONFERENCE 01/26/26",
            "weekOfDate": "2026-01-19",
            "unitPrice": 950000,
            "impressions": 45000000,
            "CPM": 21.11,
            "avails": 2.0,
            "division": "SPORTS",
            "subDivision": "SNF",
        },
    ]
    
    # NBA inventory
    NBA_INVENTORY: ClassVar[list[dict[str, Any]]] = [
        {
            "salesUnitId": 800100,
            "name": "NBA Christmas Day - Lakers vs Warriors",
            "weekOfDate": "2025-12-22",
            "unitPrice": 325000,
            "impressions": 15000000,
            "CPM": 21.67,
            "avails": 8.0,
            "division": "SPORTS",
            "subDivision": "NBA",
        },
        {
            "salesUnitId": 800105,
            "name": "NBA Primetime - 01/10/26",
            "weekOfDate": "2026-01-05",
            "unitPrice": 185000,
            "impressions": 9500000,
            "CPM": 19.47,
            "avails": 12.0,
            "division": "SPORTS",
            "subDivision": "NBA",
        },
    ]
    
    # Entertainment inventory
    ENTERTAINMENT_INVENTORY: ClassVar[list[dict[str, Any]]] = [
        {
            "salesUnitId": 850200,
            "name": "Golden Globes 2026",
            "weekOfDate": "2026-01-05",
            "unitPrice": 425000,
            "impressions": 18000000,
            "CPM": 23.61,
            "avails": 5.0,
            "division": "ENTERTAINMENT",
            "subDivision": "AWARDS",
        },
    ]
    
    @classmethod
    def get_all_inventory(cls) -> list[dict[str, Any]]:
        """Get all available inventory."""
        return cls.SNF_INVENTORY + cls.NBA_INVENTORY + cls.ENTERTAINMENT_INVENTORY
    
    @classmethod
    def filter_inventory(
        cls,
        flight_start: str,
        flight_end: str,
        division: str | None = None,
        sub_division: str | None = None,
    ) -> list[dict[str, Any]]:
        """Filter inventory by date range and division."""
        all_inventory = cls.get_all_inventory()
        
        filtered = []
        for item in all_inventory:
            week_date = item["weekOfDate"]
            
            # Check date range
            if week_date < flight_start or week_date > flight_end:
                continue
            
            # Check division
            if division and item.get("division", "").upper() != division.upper():
                continue
            
            # Check sub-division
            if sub_division and item.get("subDivision", "").upper() != sub_division.upper():
                continue
            
            # Return clean item (without internal fields)
            filtered.append({
                "salesUnitId": item["salesUnitId"],
                "name": item["name"],
                "weekOfDate": item["weekOfDate"],
                "unitPrice": item["unitPrice"],
                "impressions": item["impressions"],
                "CPM": round(item["CPM"], 5),
                "avails": item["avails"],
            })
        
        return filtered
    
    @classmethod
    def calculate_measurement(
        cls,
        linear_plan: list[dict[str, Any]],
        digital_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate cross-platform reach and frequency estimates."""
        
        # Calculate linear metrics
        linear_budget = sum(item["numUnits"] * item["unitPrice"] for item in linear_plan)
        linear_impressions = sum(item["impressions"] for item in linear_plan)
        linear_cpm = round(linear_budget / (linear_impressions / 1000), 2) if linear_impressions > 0 else 0
        
        # Estimate reach (typically 90% of impressions for live sports)
        linear_reach = int(linear_impressions * 0.9)
        linear_frequency = round(linear_impressions / linear_reach, 2) if linear_reach > 0 else 0
        
        # Calculate digital metrics
        digital_budget = sum(item["budget"] for item in digital_plan)
        digital_cpm = digital_plan[0]["CPM"] if digital_plan else 33.89  # Default streaming CPM
        digital_impressions = int(digital_budget / (digital_cpm / 1000)) if digital_cpm > 0 else 0
        
        # Digital typically has higher frequency, lower reach
        digital_reach = int(digital_impressions * 0.33)  # 33% reach rate
        digital_frequency = round(digital_impressions / digital_reach, 2) if digital_reach > 0 else 0
        
        # Cross-platform (deduplicated)
        cross_budget = linear_budget + digital_budget
        cross_impressions = linear_impressions + digital_impressions
        cross_cpm = round(cross_budget / (cross_impressions / 1000), 2) if cross_impressions > 0 else 0
        
        # Cross-platform reach is deduplicated (assume 15% overlap)
        overlap = int(min(linear_reach, digital_reach) * 0.15)
        cross_reach = linear_reach + digital_reach - overlap
        cross_frequency = round(cross_impressions / cross_reach, 2) if cross_reach > 0 else 0
        
        return {
            "linear": {
                "budget": linear_budget,
                "impressions": linear_impressions,
                "CPM": linear_cpm,
                "estReach": linear_reach,
                "estFrequency": linear_frequency,
            },
            "digital": {
                "budget": digital_budget,
                "impressions": digital_impressions,
                "CPM": digital_cpm,
                "estReach": digital_reach,
                "estFrequency": digital_frequency,
            },
            "crossPlatform": {
                "budget": cross_budget,
                "impressions": cross_impressions,
                "CPM": cross_cpm,
                "estReach": cross_reach,
                "estFrequency": cross_frequency,
            },
        }
    
    @classmethod
    def save_plan(
        cls,
        linear_plan: list[dict[str, Any]],
        digital_plan: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Save a plan and return confirmation with measurement."""
        cls.plan_counter += 1
        plan_id = cls.plan_counter
        
        measurement = cls.calculate_measurement(linear_plan, digital_plan)
        
        # Store the plan
        cls.saved_plans[str(plan_id)] = {
            "linearPlanId": plan_id,
            "linearPlan": linear_plan,
            "digitalPlan": digital_plan,
            "measurement": measurement,
            "status": "BOOKED",
            "created_at": datetime.now(UTC).isoformat(),
        }
        
        return {
            "linearPlanId": plan_id,
            "planMeasurement": measurement,
        }
    
    @classmethod
    def clear_data(cls) -> dict[str, Any]:
        """Clear all saved plans."""
        count = len(cls.saved_plans)
        cls.saved_plans.clear()
        cls.plan_counter = 100
        return {
            "success": True,
            "plans_cleared": count,
        }


# ============================================================================
# getProducts - Get Available Inventory
# ============================================================================

async def _get_products_impl(
    flight_start_date: str,
    flight_end_date: str,
    advertiser: str,
    audience: str = "P2+",
    division: str | None = None,
    sub_division: str | None = None,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """
    Implementation for getting NBCU available inventory.
    
    Args:
        flight_start_date: Start date (YYYY-MM-DD)
        flight_end_date: End date (YYYY-MM-DD)
        advertiser: Advertiser name
        audience: Target audience (default P2+)
        division: Optional division filter (SPORTS, ENTERTAINMENT, NEWS)
        sub_division: Optional sub-division filter (SNF, NBA, MLB, etc.)
    
    Returns:
        List of available inventory units
    """
    logger.info(f"📺 NBCU: Getting products for {advertiser}")
    logger.info(f"   Flight: {flight_start_date} to {flight_end_date}")
    logger.info(f"   Audience: {audience}")
    if division:
        logger.info(f"   Division: {division}")
    if sub_division:
        logger.info(f"   Sub-Division: {sub_division}")
    
    products = NBCUDataStore.filter_inventory(
        flight_start=flight_start_date,
        flight_end=flight_end_date,
        division=division,
        sub_division=sub_division,
    )
    
    logger.info(f"   Found {len(products)} available units")
    return products


async def getProducts(
    flightStartDate: str,
    flightEndDate: str,
    advertiser: str,
    audience: str = "P2+",
    division: str | None = None,
    subDivision: str | None = None,
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Get available NBCU inventory for Linear & Streaming advertising.
    
    This tool returns available advertising units across NBCU's portfolio
    including Sunday Night Football (SNF), NBA, and entertainment programming.
    
    Args:
        flightStartDate: Campaign start date (YYYY-MM-DD format)
        flightEndDate: Campaign end date (YYYY-MM-DD format)
        advertiser: Advertiser name (e.g., "Honda")
        audience: Target audience demographic (default: "P2+")
        division: Filter by division - "SPORTS", "ENTERTAINMENT", or "NEWS"
        subDivision: Filter by sub-division - "SNF", "NBA", "MLB", etc.
    
    Returns:
        List of available inventory with:
        - salesUnitId: Unique identifier for the unit
        - name: Event/program name
        - weekOfDate: Week the unit airs
        - unitPrice: Cost per :30 unit
        - impressions: Estimated P2+ impressions
        - CPM: Cost per thousand impressions
        - avails: Number of available units
    
    Example:
        getProducts(
            flightStartDate="2025-12-29",
            flightEndDate="2026-01-13",
            advertiser="Honda",
            audience="P2+",
            division="SPORTS",
            subDivision="SNF"
        )
    """
    result = await _get_products_impl(
        flight_start_date=flightStartDate,
        flight_end_date=flightEndDate,
        advertiser=advertiser,
        audience=audience,
        division=division,
        sub_division=subDivision,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# getMeasurement - Calculate Cross-Platform Reach/Frequency
# ============================================================================

async def _get_measurement_impl(
    linear_plan: list[dict[str, Any]],
    digital_plan: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Implementation for calculating cross-platform measurement.
    
    Args:
        linear_plan: List of linear (TV) units
        digital_plan: List of digital (streaming) allocations
    
    Returns:
        Cross-platform measurement with reach/frequency estimates
    """
    logger.info("📊 NBCU: Calculating cross-platform measurement")
    logger.info(f"   Linear units: {len(linear_plan)}")
    logger.info(f"   Digital allocations: {len(digital_plan)}")
    
    measurement = NBCUDataStore.calculate_measurement(linear_plan, digital_plan)
    
    logger.info(f"   Total budget: ${measurement['crossPlatform']['budget']:,}")
    logger.info(f"   Est. reach: {measurement['crossPlatform']['estReach']:,}")
    
    return measurement


async def getMeasurement(
    linearPlan: list[dict[str, Any]],
    digitalPlan: list[dict[str, Any]],
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Calculate cross-platform reach and frequency estimates for a media plan.
    
    This tool provides measurement estimates for a combined Linear + Streaming
    plan, including deduplicated cross-platform reach.
    
    Args:
        linearPlan: Array of linear (TV) plan units, each containing:
            - salesUnitId: Unit identifier from getProducts
            - weekOfDate: Week of the unit (YYYY-MM-DD)
            - numUnits: Number of :30 units to purchase
            - unitLength: Spot length in seconds (typically 30)
            - unitPrice: Price per unit
            - impressions: Total impressions for this line
        
        digitalPlan: Array of digital (streaming) allocations, each containing:
            - budget: Dollar amount allocated to streaming
            - CPM: Streaming CPM rate
            - unitLengths: Array of accepted unit lengths (e.g., [30])
    
    Returns:
        Measurement breakdown with:
        - linear: Budget, impressions, CPM, estimated reach & frequency for TV
        - digital: Budget, impressions, CPM, estimated reach & frequency for streaming
        - crossPlatform: Combined deduplicated metrics
    
    Example:
        getMeasurement(
            linearPlan=[{
                "salesUnitId": 786370,
                "weekOfDate": "2026-01-12",
                "numUnits": 2,
                "unitLength": 30,
                "unitPrice": 803620,
                "impressions": 76280000
            }],
            digitalPlan=[{
                "budget": 144561,
                "CPM": 33.89,
                "unitLengths": [30]
            }]
        )
    """
    result = await _get_measurement_impl(
        linear_plan=linearPlan,
        digital_plan=digitalPlan,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# savePlan - Book a Plan
# ============================================================================

async def _save_plan_impl(
    linear_plan: list[dict[str, Any]],
    digital_plan: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Implementation for saving/booking a plan.
    
    Args:
        linear_plan: List of linear (TV) units
        digital_plan: List of digital (streaming) allocations
    
    Returns:
        Plan confirmation with ID and measurement
    """
    logger.info("📝 NBCU: Booking plan")
    
    result = NBCUDataStore.save_plan(linear_plan, digital_plan)
    
    logger.info(f"   ✅ Plan booked: ID {result['linearPlanId']}")
    logger.info(f"   Cross-platform reach: {result['planMeasurement']['crossPlatform']['estReach']:,}")
    
    return result


async def savePlan(
    linearPlan: list[dict[str, Any]],
    digitalPlan: list[dict[str, Any]],
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Book a Linear & Streaming media plan with NBCU.
    
    This tool finalizes and books a media plan, returning a confirmation
    with plan ID and cross-platform measurement estimates.
    
    Args:
        linearPlan: Array of linear (TV) plan units, each containing:
            - salesUnitId: Unit identifier from getProducts
            - weekOfDate: Week of the unit (YYYY-MM-DD)
            - numUnits: Number of :30 units to purchase
            - unitLength: Spot length in seconds (typically 30)
            - unitPrice: Price per unit
            - impressions: Total impressions for this line
        
        digitalPlan: Array of digital (streaming) allocations, each containing:
            - budget: Dollar amount allocated to streaming
            - CPM: Streaming CPM rate
            - unitLengths: Array of accepted unit lengths (e.g., [30])
    
    Returns:
        Plan confirmation with:
        - linearPlanId: Unique plan identifier for reference
        - planMeasurement: Cross-platform reach/frequency breakdown
    
    Example:
        savePlan(
            linearPlan=[{
                "salesUnitId": 786370,
                "weekOfDate": "2026-01-12",
                "numUnits": 2,
                "unitLength": 30,
                "unitPrice": 803620,
                "impressions": 76280000
            }],
            digitalPlan=[{
                "budget": 144561,
                "CPM": 33.89,
                "unitLengths": [30]
            }]
        )
    
    Next Steps After Booking:
        1. Send creative via MediaOcean/OMNI
        2. Review Linear specs: https://together.nbcuni.com/ad-specs/
        3. Review Streaming specs: https://together.nbcuni.com/ad-specs/streaming/
        4. Weekly pacing/delivery reports will be provided
    """
    result = await _save_plan_impl(
        linear_plan=linearPlan,
        digital_plan=digitalPlan,
        ctx=ctx,
    )
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# clearNBCUDemoData - Reset Demo State
# ============================================================================

async def _clear_nbcu_demo_data_impl(
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Implementation for clearing NBCU demo data."""
    logger.info("🧹 NBCU: Clearing demo data")
    result = NBCUDataStore.clear_data()
    return result


async def clearNBCUDemoData(
    ctx: Context | None = None,
    super_access: bool = False,
) -> ToolResult:
    """
    Clear all NBCU demo plan data.
    
    This tool resets the NBCU simulation state, removing all saved plans.
    Use this to start fresh before running a new demo.
    
    Returns:
        Confirmation with number of plans cleared
    
    Example:
        clearNBCUDemoData()
    """
    result = await _clear_nbcu_demo_data_impl(ctx=ctx)
    return ToolResult(content=str(result), structured_content=result)


# ============================================================================
# Raw A2A Functions
# ============================================================================

async def get_products_raw(
    flight_start_date: str,
    flight_end_date: str,
    advertiser: str,
    audience: str = "P2+",
    division: str | None = None,
    sub_division: str | None = None,
    ctx: Context | None = None,
) -> list[dict[str, Any]]:
    """A2A raw function for getProducts."""
    return await _get_products_impl(
        flight_start_date=flight_start_date,
        flight_end_date=flight_end_date,
        advertiser=advertiser,
        audience=audience,
        division=division,
        sub_division=sub_division,
        ctx=ctx,
    )


async def get_measurement_raw(
    linear_plan: list[dict[str, Any]],
    digital_plan: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for getMeasurement."""
    return await _get_measurement_impl(
        linear_plan=linear_plan,
        digital_plan=digital_plan,
        ctx=ctx,
    )


async def save_plan_raw(
    linear_plan: list[dict[str, Any]],
    digital_plan: list[dict[str, Any]],
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for savePlan."""
    return await _save_plan_impl(
        linear_plan=linear_plan,
        digital_plan=digital_plan,
        ctx=ctx,
    )


async def clear_nbcu_demo_data_raw(
    ctx: Context | None = None,
) -> dict[str, Any]:
    """A2A raw function for clearNBCUDemoData."""
    return await _clear_nbcu_demo_data_impl(ctx=ctx)

