# Deployment Process

## CRITICAL: Production Safety

If this is a live production application, broken deployments directly impact real users.

## Deployment Workflow

### 1. Deploy to Test/Staging First

**Always deploy to test/staging before production:**

```bash
# Example for various platforms:
npx wrangler deploy --env test          # Cloudflare Workers
npm run deploy:staging                   # Custom scripts
vercel --prod=false                      # Vercel preview
```

### 2. Validate in Test/Staging

Run automated tests:
```bash
npm test
```

Manual validation checklist:
- [ ] Core functionality works
- [ ] No console errors in browser
- [ ] Mobile/responsive layout works
- [ ] API endpoints respond correctly
- [ ] Authentication/authorization works

### 3. Deploy to Production

**Only after test/staging validation passes:**

```bash
# Example for various platforms:
npx wrangler deploy --env production     # Cloudflare Workers
npm run deploy:production                # Custom scripts
vercel --prod                            # Vercel production
```

### 4. Post-Deployment Verification

```bash
# Monitor logs
npx wrangler tail --env production       # Cloudflare
vercel logs                              # Vercel

# Smoke test
curl https://your-app.com/health
```

## Rollback Procedure

If production deployment fails:

```bash
# View previous versions
npx wrangler deployments list --env production

# Rollback
npx wrangler rollback --env production
```

## Environment Comparison

| Environment | Purpose |
|-------------|---------|
| Development | Local development, break things freely |
| Test/Staging | Pre-production validation |
| Production | Live user traffic |

## What NOT to Deploy

The following files should **never** be committed or deployed:

- Chat logs (`*-chat-*.md`)
- Scratch notes (`scratch.txt`)
- Temporary exports (`*.csv`, `*.pdf`)
- Local state directories (`.wrangler/`, `.vercel/`)
- Environment files with secrets (`.env`)

## Emergency Checklist

If production is broken:
1. Check logs for errors
2. Rollback to previous version
3. Review recent commits for breaking changes
4. Fix forward only after root cause identified

