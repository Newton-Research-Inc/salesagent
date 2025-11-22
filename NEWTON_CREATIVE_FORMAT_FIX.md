# Newton Creative Format Fix

## What Happened

Newton got a confusing error when trying to create a media buy. Looking at the MCP responses, I found **Newton is making a creative format mistake**.

## The Problem

**Error Newton got:**
```
assets.width: Input should be a valid dictionary
assets.height: Input should be a valid dictionary
```

**What Newton is doing (WRONG):**
```python
"assets": {
    "image": {
        "url": "https://placeholder.com/nike_728x90.jpg",
        "width": 728,
        "height": 90
    },
    "width": 728,   # ❌ WRONG - causes validation error
    "height": 90    # ❌ WRONG - causes validation error
}
```

**What Newton should do (CORRECT):**
```python
"assets": {
    "image": {
        "url": "https://placeholder.com/nike_728x90.jpg",
        "width": 728,
        "height": 90
    }
    # NO width/height at assets level
}
```

## Why This Happens

The AdCP spec says:
- `assets` is an **object containing asset types** (image, video, audio, etc.)
- Each **asset type** (e.g., `image`) has its own width/height
- Width/height should **ONLY** be inside the asset type object
- Width/height at the `assets` level is **invalid**

Newton seems to be duplicating the width/height at both levels, probably trying to be helpful but actually violating the spec.

## The Flow of Errors

1. **First attempt**: Newton tries to create media buy
   - Error: "Reference creative missing dimensions"
   - Reason: Creatives weren't synced yet (or sync failed)

2. **Newton re-syncs creatives** with width/height at assets level
   - Error: "assets.width: Input should be a valid dictionary"
   - Reason: width/height should NOT be at assets level

3. **Newton tries media buy again**
   - Either succeeds (if creatives were synced earlier)
   - Or fails with "duplicate buyer_ref" (if it succeeded the first time)

## What I Fixed

### 1. Updated Workflow Guide
📄 `newton/CONTAINER/workflows/public/adcp_media_buying/WORKFLOW.md`

**Added clear warning section:**
```python
**⚠️ Common Creative Sync Mistake:**
# ❌ WRONG - Do NOT add width/height at assets level
"assets": {
    "image": {"url": "...", "width": 728, "height": 90},
    "width": 728,   # ❌ ERROR
    "height": 90    # ❌ ERROR
}

# ✅ CORRECT - width/height ONLY in nested asset object
"assets": {
    "image": {"url": "...", "width": 728, "height": 90}
}
```

### 2. Updated Quick Reference
📄 `newton/CONTAINER/workflows/public/adcp_media_buying/QUICK_REFERENCE.md`

**Changes:**
- Added clear comments in code example about where width/height go
- Added to Common Errors table:
  - "assets.width: Input should be a valid dictionary"
  - "Reference creative missing dimensions"

### 3. Error Handling Guidance

**If Newton sees:**
- `"assets.width: Input should be a valid dictionary"` → Remove width/height from assets level
- `"Reference creative missing dimensions"` → Re-sync creatives with correct format
- `"duplicate buyer_ref"` → Campaign already exists (check delivery instead)

## Correct Creative Format Template

```python
creatives = [
    {
        "creative_id": "unique_id",
        "name": "Campaign Name - Format",
        "format_id": "display_728x90",  # Standard IAB format
        "click_through_url": "https://brand.com",
        "preview_url": "https://placeholder.com/ad.jpg",
        "assets": {
            "image": {  # ✅ width/height go HERE
                "url": "https://placeholder.com/ad.jpg",
                "width": 728,
                "height": 90
            }
            # ❌ NO width/height here at assets level
        }
    }
]

# Sync to sales agent
result = mcp_24_sync_creatives(creatives=creatives)
```

## Testing the Fix

Newton should:

1. **Clear any existing media buys** (if needed for clean test)
2. **Sync creatives** using the CORRECT format (width/height only in image object)
3. **Verify sync succeeded** - check result for "action": "created" or "updated"
4. **Create media buy** with the synced creative_ids
5. **Verify media buy created** - should get media_buy_id back

## Why the Duplicate Error is Actually Good

If Newton sees "duplicate buyer_ref", it means:
- ✅ The campaign **was successfully created**
- ✅ The system is **preventing accidental duplicates**
- ✅ Newton should **check delivery status** instead of creating again

This is **correct behavior** - better than silently creating duplicate campaigns!

## Summary

**Problem**: Newton adding width/height at wrong level in creative assets  
**Solution**: Updated workflow guides with clear warnings and correct examples  
**Impact**: Newton should now sync creatives successfully and create media buys  

**Tell Newton**: "Use the updated workflow examples - width and height go INSIDE the image object, not at the assets level."

