# Final Bug Fix: SQLAlchemy Session Detachment (2025-11-19)

## 🐛 Bug #4: SQLAlchemy DetachedInstanceError

### The Problem

Newton encountered:
```
DetachedInstanceError: Instance <Creative at 0xffffa7ee3a70> is not bound to a Session; 
attribute refresh operation cannot proceed
```

**Root Cause**: We were accessing `Creative` object attributes (`creative.data`, `creative.format`, `creative.name`) AFTER calling `adapter.add_creative_assets()`, which caused the object to become detached from the SQLAlchemy session.

### Where It Failed

**Location**: `src/core/tools/media_buy_create.py` lines 2847-2941

**The Sequence**:
1. Line 2796: Query creatives from database
2. Line 2847: Access `creative.data.get("platform_creative_id")` ✅ OK (still in session)
3. Line 2916-2920: Call `adapter.add_creative_assets()` ⚠️ **CAUSES DETACHMENT**
4. Line 2927: Try to access `creative.data.get(...)` again ❌ **FAILS - object detached!**

### The Fix

**Pre-load all creative attributes** before calling the adapter:

```python
# ⚠️ CRITICAL: Access all creative attributes NOW before any adapter calls
# to avoid SQLAlchemy DetachedInstanceError
creative_data = dict(creative.data) if creative.data else {}
creative_format = str(creative.format)
creative_name = creative.name

# Now use these variables instead of creative.data, creative.format, creative.name
```

**Changes Made**:

1. **Line 2848-2851**: Pre-load creative attributes into Python variables
   ```python
   creative_data = dict(creative.data) if creative.data else {}
   creative_format = str(creative.format)
   creative_name = creative.name
   ```

2. **Line 2872**: Use `creative_format` instead of `str(creative.format)`
   ```python
   format_spec = get_cached_format(creative_format)
   ```

3. **Line 2897**: Use `creative_name` instead of `creative.name`
   ```python
   "name": creative_name or f"Creative {creative.creative_id}",
   ```

4. **Lines 2933-2947**: Use `creative_data` dict instead of `creative.data`
   ```python
   if not creative_data.get("platform_creative_id"):
       creative_data["platform_creative_id"] = uploaded_status.creative_id
       creative.data = creative_data  # Write back to DB
   ```

### Why This Matters

SQLAlchemy lazy-loads JSON columns like `creative.data`. When you access them:
1. **Inside session context**: ✅ Works - SQLAlchemy loads from DB
2. **Outside session context** (after adapter calls, commits, etc.): ❌ Fails - object detached

**Solution**: Load everything you need upfront, store in regular Python variables.

---

## 📊 Complete Bug Summary

| # | Bug | Symptom | Fix | Newton Hit? |
|---|-----|---------|-----|-------------|
| **1** | Variable scoping (pending) | Wrong loop variable | Initialize + correct variable | ❌ No |
| **2** | Package.get() (auto) | `'Package' object has no attribute 'get'` | Type checking | ❌ No |
| **3** | Asset field name | `CREATIVE_UPLOAD_FAILED ... 'id'` | Add `asset["id"]` | ✅ Yes |
| **4** | Session detachment | `DetachedInstanceError` | Pre-load attributes | ✅ **Yes (most recent)** |

---

## ✅ All Bugs Fixed

**Final Status**:
- ✅ Bug #1: Variable scoping (pending approval path)
- ✅ Bug #2: Package type checking (auto-approval path)
- ✅ Bug #3: Asset field name mismatch
- ✅ Bug #4: SQLAlchemy session detachment ⭐ **LATEST FIX**

**ESPN agent rebuilt** with all 4 bugs fixed

**Database clean** - ready for testing

---

## 🚀 Expected Behavior Now

Newton should complete the entire campaign creation flow:

1. ✅ Sync creatives successfully
2. ✅ Create media buy with `media_buy_id`
3. ✅ Pre-load creative attributes (no detachment!)
4. ✅ Upload creatives to GAM (no 'id' error!)
5. ✅ Update creative with `platform_creative_id`
6. ✅ Create assignments
7. ✅ Return clean success response

**Newton's next attempt should work perfectly!** 🎯

---

## 🎓 SQLAlchemy Lesson

**Rule**: Always access ORM object attributes BEFORE calling external services (adapters, APIs, etc.) that might trigger session flushes/commits.

**Pattern**:
```python
# ✅ CORRECT
data = dict(obj.data)  # Load now
format_str = str(obj.format)  # Load now
# ... call adapter ...
# Use data and format_str (safe - detached from session)

# ❌ WRONG
# ... call adapter ...
value = obj.data.get("key")  # Lazy load AFTER adapter - FAILS!
```

---

**Files Changed**:
- `src/core/tools/media_buy_create.py`:
  - Lines 2848-2851: Pre-load creative attributes
  - Line 2872: Use `creative_format`
  - Line 2897: Use `creative_name`
  - Lines 2933-2947: Use `creative_data` dict

**Status**: ✅ **READY FOR NEWTON - AGAIN!** 🚀

