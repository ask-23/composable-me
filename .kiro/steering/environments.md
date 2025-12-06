# Environment Strategy

## Core Principle

**NEVER test, experiment, or pollute production data.** Production is for real users only.

## Three-Environment Strategy

### 1. Development (Local)
**Purpose:** Local development and unit testing

**Rules:**
- All feature development happens here
- Unit tests run against local/mock data
- No real user data
- Fast iteration, break things freely

### 2. Staging/Test
**Purpose:** Pre-production validation with production-like setup

**Rules:**
- Deploy here BEFORE production
- Run integration and E2E tests here
- Load/stress testing happens here
- Can be broken/reset without consequences
- NO real customer data (use synthetic data)

### 3. Production
**Purpose:** Live customer-facing application

**Rules:**
- **NEVER test here**
- **NEVER create fake data here**
- **NEVER run experiments here**
- **NEVER run load tests here**
- Only real customer data
- Deploy only after staging validation
- Monitor closely after deployment

## Git Workflow

```
feature branch → local testing → staging deploy → validation → production deploy
     ↓              ↓                ↓                ↓              ↓
  local data     local data     staging data     staging data   production data
```

## Testing Strategy by Environment

### Development
- Unit tests
- Component tests
- Local integration tests
- Fast feedback loop

### Staging
- End-to-end tests
- Load tests
- Stress tests
- Integration tests with external services
- Performance testing

### Production
- Monitoring only
- Real user traffic
- No testing
- No experiments

## Enforcement

**Pre-commit Checks:**
- Warn if deploying to production without staging validation
- Block test data creation in production code

**Code Review:**
- No hardcoded production credentials
- No test data generators in production code
- Environment-specific configuration only

## Summary

**Golden Rule:** Production is sacred. Test in dev, validate in staging, deploy to production only when confident.

