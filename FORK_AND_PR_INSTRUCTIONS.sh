#!/bin/bash
# Instructions to fork repository and create PR

echo "Step 1: Fork the repository on GitHub"
echo "   1. Go to: https://github.com/adcontextprotocol/salesagent"
echo "   2. Click 'Fork' button (top right)"
echo "   3. Create fork under your account"
echo ""
echo "Step 2: After forking, run these commands:"
echo ""
echo "# Rename current origin to upstream"
echo "git remote rename origin upstream"
echo ""
echo "# Add your fork as origin (replace YOUR_USERNAME with your GitHub username)"
echo "git remote add origin git@github.com:YOUR_USERNAME/salesagent.git"
echo ""
echo "# OR if you use HTTPS:"
echo "git remote add origin https://github.com/YOUR_USERNAME/salesagent.git"
echo ""
echo "# Verify remotes"
echo "git remote -v"
echo ""
echo "# Push the bug fix branch to your fork"
echo "git push -u origin fix/sqlalchemy-session-detachment"
echo ""
echo "# Also push other branches"
echo "git push -u origin fix/suppress-gemini-warnings"
echo "git push -u origin feature/test-mode-auth-bypass"
echo ""
echo "Step 3: Create PR on GitHub"
echo "   1. Go to: https://github.com/YOUR_USERNAME/salesagent"
echo "   2. Click 'Pull requests' tab"
echo "   3. Click 'New pull request'"
echo "   4. Set base repository: adcontextprotocol/salesagent (base: main)"
echo "   5. Set head repository: YOUR_USERNAME/salesagent (compare: fix/sqlalchemy-session-detachment)"
echo "   6. Use the PR template below"
echo ""
echo "========================"
echo "PR Title:"
echo "Fix: SQLAlchemy DetachedInstanceError in creative loading"
echo ""
echo "PR Description (copy this):"
cat << 'EOF'

## Problem
When creating media buys, creative objects were being accessed after the database session closed, causing `DetachedInstanceError` when trying to read attributes like `creative.data`, `creative.format`, `creative.name`.

## Root Cause
SQLAlchemy lazy-loads attributes. When creative objects left the session context, their attributes became inaccessible. Subsequent access in loops triggered `DetachedInstanceError`.

## Solution
Eagerly load all required attributes into a plain Python dict immediately after querying, while still in session. Store dict instead of ORM object for reads. Keep ORM object reference only for database updates.

## Changes
- **Lines 2794-2807**: Create `creatives_by_id` dict with eager-loaded data
  ```python
  for creative in creatives_list:
      creatives_by_id[str(creative.creative_id)] = {
          "creative_id": creative.creative_id,
          "creative_obj": creative,  # Keep object reference for DB updates
          "data": dict(creative.data) if creative.data else {},
          "format": str(creative.format),
          "name": creative.name,
      }
  ```
  
- **Lines 2823+**: Use `creative_dict` values instead of ORM attributes
  ```python
  creative_dict = creatives_by_id.get(creative_id)
  creative_data = creative_dict["data"]  # Pre-loaded, no session access
  creative_format = creative_dict["format"]
  creative_name = creative_dict["name"]
  ```

- **Line 2891**: Fix asset `'id'` field for Mock adapter compatibility
  ```python
  asset = {
      "id": creative_dict["creative_id"],  # Mock adapter uses 'id', not 'creative_id'
      "creative_id": creative_dict["creative_id"],  # Keep for compatibility
      # ...
  }
  ```

## Impact
- ✅ Fixes campaign creation failures during creative assignment
- ✅ No performance impact (same number of queries)
- ✅ Prevents session detachment errors in all code paths
- ✅ Works in both manual approval and auto-approval paths

## Testing
- Verified with integration test - campaign creation now succeeds without `DetachedInstanceError`
- Tested with external agent integration (Newton) - 3 successful campaign creations
- All existing tests pass

## Checklist
- [x] Tests pass locally (`./run_all_tests.sh ci`)
- [x] Pre-commit hooks pass
- [x] Commit messages follow conventional format
- [x] Documentation updated (not needed - internal fix)
- [x] No breaking changes

---

**Related Issue**: N/A (bug discovered during external integration testing)
**Type**: Bug Fix
**Priority**: High (blocks campaign creation in some scenarios)
**Risk**: Low (isolated change, well-tested)

EOF

