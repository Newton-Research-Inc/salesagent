# Fork Setup Complete - Next Steps

## ✅ Completed Tasks

### 1. Repository Fork Structure ✅
Your fork is now properly set up with all necessary branches:

```
danf-newton/salesagent (your fork)
├── main (synced with upstream)
├── production (AWS production deployment target)
├── staging (AWS staging deployment target)
├── demo/newton-integration (Newton-specific demo code)
├── fix/sqlalchemy-session-detachment (bug fix for upstream PR)
├── fix/suppress-gemini-warnings (bug fix for upstream PR)
├── feature/test-mode-auth-bypass (private feature)
└── backup/all-bug-fixes (safety backup)
```

### 2. All Branches Pushed ✅
All your local branches are now on GitHub:
- https://github.com/danf-newton/salesagent/branches

### 3. Demo Code Organized ✅
Newton integration code is in `demo/newton-integration` branch with:
- Multi-tenant testing setup (`docker-compose.testing.yml`)
- Demo scripts (`scripts/demo/`)
- Documentation (`NEWTON_*.md`, `DEMO_*.md`)
- AWS migration plan

---

## 🎯 Next Steps (In Order)

### Step 4: Create Upstream PRs for Bug Fixes

#### PR #1: SQLAlchemy DetachedInstanceError Fix ⏳
**Priority: HIGH** - Critical bug fix

1. Go to: https://github.com/danf-newton/salesagent/compare
2. Set up PR:
   - **Base repository**: `adcontextprotocol/salesagent`
   - **Base branch**: `main`
   - **Head repository**: `danf-newton/salesagent`
   - **Compare branch**: `fix/sqlalchemy-session-detachment`

3. **Title**: 
   ```
   Fix: SQLAlchemy DetachedInstanceError in creative loading
   ```

4. **Description**: Copy from `FORK_AND_PR_INSTRUCTIONS.sh` or use this:

```markdown
## Problem
When creating media buys, creative objects were being accessed after the database session closed, causing `DetachedInstanceError` when trying to read attributes like `creative.data`, `creative.format`, `creative.name`.

## Root Cause
SQLAlchemy lazy-loads attributes. When creative objects left the session context, their attributes became inaccessible. Subsequent access in loops triggered `DetachedInstanceError`.

## Solution
Eagerly load all required attributes into a plain Python dict immediately after querying, while still in session. Store dict instead of ORM object for reads. Keep ORM object reference only for database updates.

## Changes
- **Lines 2794-2807**: Create `creatives_by_id` dict with eager-loaded data
- **Lines 2823+**: Use `creative_dict` values instead of ORM attributes  
- **Line 2891**: Fix asset `'id'` field for Mock adapter compatibility

## Impact
- ✅ Fixes campaign creation failures during creative assignment
- ✅ No performance impact (same number of queries)
- ✅ Prevents session detachment errors in all code paths

## Testing
Verified with integration test - campaign creation now succeeds without `DetachedInstanceError`.

## Checklist
- [x] Tests pass locally
- [x] Pre-commit hooks pass
- [x] No breaking changes
```

---

#### PR #2: Suppress Gemini Warnings ⏳
**Priority: MEDIUM** - UX improvement

1. Go to: https://github.com/danf-newton/salesagent/compare
2. Set up PR:
   - **Base repository**: `adcontextprotocol/salesagent`
   - **Base branch**: `main`
   - **Head repository**: `danf-newton/salesagent`
   - **Compare branch**: `fix/suppress-gemini-warnings`

3. **Title**:
   ```
   Fix: Suppress Gemini API key warnings when not configured
   ```

4. **Description**:

```markdown
## Problem
When `GEMINI_API_KEY` is not configured, the AI test orchestrator prints warning messages on every failed LLM call. These warnings confused external agents into thinking operations had failed, when actually the operation succeeded but AI enhancement was simply unavailable.

## Solution
Suppress warnings specifically for API key errors (`'API_KEY_INVALID'`, `'API key not valid'`). These are expected when Gemini is not configured. Other genuine errors are still logged for debugging.

## Impact
- ✅ Cleaner logs when Gemini is not configured (expected state)
- ✅ External agents no longer confused by benign warnings
- ✅ Actual errors still logged for debugging
- ✅ No functional changes - behavior unchanged

## Testing
Verified with external agent integration - operations succeed without confusing warning messages.

## Checklist
- [x] Tests pass locally
- [x] Pre-commit hooks pass
- [x] No breaking changes
```

---

### Step 5: Set Up GitHub Actions for AWS CI/CD

Create these workflow files in your fork:

#### File 1: `.github/workflows/test.yml`
Run tests on all PRs and pushes:

```yaml
name: Test

on:
  pull_request:
    branches: [main, staging, production]
  push:
    branches: [main, staging, production]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/testdb
          GEMINI_API_KEY: dummy-key-for-tests
          GOOGLE_CLIENT_ID: dummy-client-id
          GOOGLE_CLIENT_SECRET: dummy-secret
          SUPER_ADMIN_EMAILS: test@example.com
        run: |
          uv run pytest tests/ -v --cov=. --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
```

#### File 2: `.github/workflows/deploy-staging.yml`
Deploy to AWS staging environment:

```yaml
name: Deploy Staging

on:
  push:
    branches: [staging]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: salesagent-staging
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster salesagent-staging \
            --service salesagent-staging-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster salesagent-staging \
            --services salesagent-staging-service
```

#### File 3: `.github/workflows/deploy-production.yml`
Deploy to AWS production environment (with manual approval):

```yaml
name: Deploy Production

on:
  push:
    branches: [production]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: salesagent-production
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster salesagent-production \
            --service salesagent-production-service \
            --force-new-deployment
      
      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster salesagent-production \
            --services salesagent-production-service
      
      - name: Run smoke tests
        run: |
          curl -f https://api.yourdomain.com/health || exit 1
```

#### GitHub Secrets to Configure

Go to: https://github.com/danf-newton/salesagent/settings/secrets/actions

Add these secrets:
- `AWS_ACCESS_KEY_ID` - Your AWS IAM access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS IAM secret key
- `GEMINI_API_KEY` - Your Gemini API key (if using)
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth secret
- `SUPER_ADMIN_EMAILS` - Admin email addresses

---

### Step 6: Configure AWS Infrastructure with Terraform

**Option A: Quick Start (Manual AWS Setup)**
1. Create AWS account
2. Manually create:
   - ECS cluster
   - RDS PostgreSQL instance
   - Application Load Balancer
   - ECR repositories (salesagent-staging, salesagent-production)

**Option B: Infrastructure as Code (Recommended)**
Follow the Terraform guide in `AWS_MIGRATION_PLAN.md` Part F.

Key resources to create:
1. **VPC with public/private subnets**
2. **RDS PostgreSQL** (db.t4g.micro for staging, db.t4g.small for production)
3. **ECS Fargate cluster**
4. **Application Load Balancer**
5. **ECR repositories**
6. **CloudWatch log groups**
7. **Secrets Manager** (for credentials)

---

## Deployment Workflow

Once GitHub Actions and AWS are set up:

### Daily Development:
```bash
# 1. Work on feature branch
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "Add: my feature"
git push origin feature/my-feature

# 2. Create PR to staging
# Merge via GitHub UI

# 3. Staging auto-deploys when merged
# Test on staging environment

# 4. If staging tests pass, PR to production
# Merge via GitHub UI (requires approval)

# 5. Production auto-deploys
```

### Weekly Upstream Sync:
```bash
# Pull latest from open source
git checkout main
git fetch upstream
git merge upstream/main
git push origin main

# Update staging
git checkout staging
git merge main
git push origin staging  # Auto-deploys to AWS staging

# Update production (after testing)
git checkout production
git merge main
git push origin production  # Auto-deploys to AWS production
```

---

## Current Branch Status

Run `git branch -a` to see all branches:
```
* demo/newton-integration
  backup/all-bug-fixes
  feature/test-mode-auth-bypass
  fix/sqlalchemy-session-detachment
  fix/suppress-gemini-warnings
  main
  production
  staging
  remotes/origin/...
  remotes/upstream/main
```

---

## Quick Reference Commands

### Sync with Upstream
```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### Deploy to Staging
```bash
git checkout staging
git merge main
git push origin staging  # Triggers GitHub Actions deploy
```

### Deploy to Production
```bash
git checkout production
git merge staging  # Or merge specific feature branch
git push origin production  # Triggers GitHub Actions deploy (requires approval)
```

### View Your Fork
- **GitHub**: https://github.com/danf-newton/salesagent
- **Branches**: https://github.com/danf-newton/salesagent/branches
- **Actions**: https://github.com/danf-newton/salesagent/actions

---

## Summary

✅ **Completed**:
1. Repository forked
2. All branches pushed
3. Production and staging branches created
4. Demo branch with Newton integration created

⏳ **Next** (in order):
1. Create PR #1: SQLAlchemy fix → upstream
2. Create PR #2: Gemini warnings → upstream
3. Set up GitHub Actions workflows
4. Configure AWS infrastructure
5. Deploy to staging
6. Deploy to production

---

## Resources

- **Your Fork**: https://github.com/danf-newton/salesagent
- **Upstream**: https://github.com/adcontextprotocol/salesagent
- **AWS Migration Plan**: `AWS_MIGRATION_PLAN.md`
- **Demo Guide**: `docs/demo/COMPLETE_DEMO_GUIDE.md`

---

**You're all set! 🎉**

Next immediate action: **Create the two upstream PRs** for your bug fixes!

