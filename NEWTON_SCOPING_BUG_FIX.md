# Variable Scoping Bug Fix (2025-11-19)

## 🐛 The Bug

Newton was getting this error on `create_media_buy`:
```
Failed to create media buy: 'Package' object has no attribute 'get'
```

**BUT** - the media buy was actually being created successfully! The error happened AFTER creation during database package record creation.

## 🔍 Root Cause

In `src/core/tools/media_buy_create.py` (pending approval code path), there were **two critical variable scoping bugs**:

### Bug 1: Wrong Variable Used (Line ~2056)
```python
# ❌ WRONG - Using pkg_data from PREVIOUS loop (lines 1869-1898)
for pkg_obj in pending_packages:
    # ...
    db_package = DBMediaPackage(
        package_id=pkg_data["package_id"],  # ❌ pkg_data is from a different loop!
        ...
    )
```

**Fix:**
```python
# ✅ CORRECT - Use pkg_obj from CURRENT loop
for pkg_obj in pending_packages:
    # ...
    db_package = DBMediaPackage(
        package_id=pkg_obj.package_id,  # ✅ Correct variable!
        ...
    )
```

### Bug 2: Uninitialized Variables (Lines ~2004, ~2048)
```python
# ❌ WRONG - pricing_info_for_package and budget_value not initialized
for pkg_obj in pending_packages:
    for idx, req_pkg in enumerate(req.packages):
        if idx == pending_packages.index(pkg_obj):
            pricing_info_for_package = ...  # Only set if match found
            budget_value = ...
    
    # If inner loop didn't match, these are undefined!
    if pricing_info_for_package:  # ❌ NameError if not set
        bid_price = pricing_info_for_package.get("bid_price")  # ❌ Undefined
```

**Fix:**
```python
# ✅ CORRECT - Initialize variables before inner loop
for pkg_obj in pending_packages:
    pricing_info_for_package: dict[str, Any] | None = None
    budget_value: dict[str, Any] | None = None
    
    for idx, req_pkg in enumerate(req.packages):
        if idx == pending_packages.index(pkg_obj):
            pricing_info_for_package = ...
            budget_value = ...
    
    # Now safe to use even if inner loop didn't match
    if pricing_info_for_package:
        bid_price = pricing_info_for_package.get("bid_price")  # ✅ Works
```

## ✅ Impact

**Before Fix:**
- ❌ First `create_media_buy` call: Created campaign but returned error
- ❌ Newton retried → Got "duplicate" error (campaign already existed)
- ❌ Newton confused: "Failed" but campaign exists

**After Fix:**
- ✅ First `create_media_buy` call: Creates campaign AND returns success
- ✅ Newton gets proper success response
- ✅ No confusion, no retries

## 🧪 Testing

After rebuild:
```bash
cd /Users/danfinkel/github/opensource/salesagent
docker-compose -f docker-compose.testing.yml up -d --build espn-agent
```

Newton should now successfully create campaigns on first attempt! 🎉

## 📝 Files Changed

- `src/core/tools/media_buy_create.py`:
  - Lines ~1993-1994: Initialize `pricing_info_for_package` and `budget_value`
  - Line ~2060: Changed `pkg_data["package_id"]` to `pkg_obj.package_id`

## 🚀 Next Steps

Tell Newton to try creating the Nike campaign again - should work on first attempt now!

