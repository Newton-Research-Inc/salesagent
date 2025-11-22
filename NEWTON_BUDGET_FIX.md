# Newton Budget Fix - AdCP v2.2.0

## The Problem
Newton is getting "budget must be positive" error because budget is being provided at the wrong level or in the wrong format.

## AdCP v2.2.0 Spec: Budget is PACKAGE-LEVEL

**❌ WRONG - Old format with pricing object:**
```python
packages=[{
    "package_id": "nike_homepage",
    "product_id": "espn_homepage_leaderboard",
    "creative_ids": ["nike_air_jordan_leaderboard"],
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "pricing": {  # ❌ This format is DEPRECATED
        "model": "cpm",
        "amount": 25.00,
        "currency": "USD"
    },
    "guaranteed_impressions": 1500000,
    "pacing": "even"
}]
```

**✅ CORRECT - AdCP v2.2.0 format with package budget:**
```python
packages=[{
    "package_id": "nike_homepage",
    "product_id": "espn_homepage_leaderboard",
    "creative_ids": ["nike_air_jordan_leaderboard"],
    "start_date": "2024-12-01",
    "end_date": "2024-12-31",
    "budget": 37500.0,  # ✅ Budget as float at package level
    "impressions": 1500000,  # Note: use "impressions" not "guaranteed_impressions"
    "pacing": "even"
}]
```

## Key Changes

1. **Remove `pricing` object** - It's deprecated
2. **Add `budget` field** - Float value at package level (e.g., `37500.0`)
3. **Use `impressions`** - Not `guaranteed_impressions`
4. **Use `start_date` and `end_date`** - Simple strings (YYYY-MM-DD) are fine

## Full Example for Newton

```python
# Nike Air Jordan Campaign on ESPN
# Total budget: $61,500 across 3 packages

result = mcp_24_create_media_buy(
    buyer_ref="nike_air_jordan_q4_2025",
    brand_manifest={"name": "Nike", "url": "https://nike.com"},
    promoted_offering="Nike Air Jordan",
    start_time="2024-12-01T00:00:00-05:00",  # US/Eastern timezone
    end_time="2024-12-31T23:59:59-05:00",    # US/Eastern timezone
    packages=[
        {
            "package_id": "nike_homepage",
            "product_id": "espn_homepage_leaderboard",
            "creative_ids": ["nike_air_jordan_leaderboard"],
            "start_date": "2024-12-01",
            "end_date": "2024-12-31",
            "budget": 37500.0,  # ✅ Package budget (1.5M impressions * $25 CPM / 1000)
            "impressions": 1500000,
            "pacing": "even"
        },
        {
            "package_id": "nike_sidebar",
            "product_id": "espn_live_game_sidebar",
            "creative_ids": ["nike_air_jordan_rectangle"],
            "start_date": "2024-12-01",
            "end_date": "2024-12-31",
            "budget": 15000.0,  # ✅ Package budget (750K impressions * $20 CPM / 1000)
            "impressions": 750000,
            "pacing": "even"
        },
        {
            "package_id": "nike_mobile",
            "product_id": "espn_mobile_banner",
            "creative_ids": ["nike_air_jordan_mobile"],
            "start_date": "2024-12-01",
            "end_date": "2024-12-31",
            "budget": 9000.0,  # ✅ Package budget (600K impressions * $15 CPM / 1000)
            "impressions": 600000,
            "pacing": "even"
        }
    ]
)
```

## Budget Calculation

For CPM pricing:
```python
budget = (impressions / 1000) * cpm

# Examples:
# Homepage: (1,500,000 / 1000) * $25 = $37,500
# Sidebar:  (750,000 / 1000) * $20 = $15,000
# Mobile:   (600,000 / 1000) * $15 = $9,000
# Total: $61,500
```

## Required Fields per Package

- ✅ `package_id` - Unique identifier (string)
- ✅ `product_id` - Product from get_products (string)
- ✅ `creative_ids` - Creatives from sync_creatives (array)
- ✅ `start_date` - YYYY-MM-DD (string)
- ✅ `end_date` - YYYY-MM-DD (string)
- ✅ `budget` - Total package budget (float) **REQUIRED**
- ✅ `impressions` - Goal impressions (integer)
- ✅ `pacing` - "even" or "asap" (string)

## What NOT to Include

- ❌ `pricing` object (deprecated)
- ❌ `guaranteed_impressions` (use `impressions`)
- ❌ Top-level `budget` or `total_budget` (only package-level)
- ❌ `pricing_option_id` (not needed - pricing is derived from product)

