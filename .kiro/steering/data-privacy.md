# Data Privacy and Security

## CRITICAL: Personal Data Protection

Applications often collect **personal identifiable information (PII)** including:
- Full names
- Email addresses
- Phone numbers
- IP addresses
- Signatures
- Payment information

**All legal and moral obligations for data protection apply.**

## Core Principles

### 1. Minimize Data Exposure
- **Never log PII** to console, error messages, or monitoring systems
- **Never include PII in test data** or examples in code/documentation
- **Never commit real user data** to git repository
- **Never share production data** in chat logs, screenshots, or external tools

### 2. Secure Data Handling
- PII must only be accessed when absolutely necessary for the feature
- Use placeholder data in examples: `user@example.com`, `Test User`
- Redact PII from error messages and logs
- Production data stays in production - never export without explicit authorization

### 3. Data Access Controls
- Test environment uses separate data (no production data)
- Production access requires explicit authorization
- Export operations must be logged and justified
- Sensitive exports encrypted in transit/at rest

## Prohibited Actions

### ❌ NEVER Do This
- Log user emails or names to console
- Include real user data in code comments or documentation
- Copy production data to test environment
- Share exports via unsecured channels
- Use production data for testing or debugging
- Commit files containing real user information
- Display PII in error messages shown to users
- Store PII in browser localStorage unnecessarily
- Send PII to third-party services without consent

### ✅ Always Do This
- Use `user@example.com` and `Test User` in examples
- Redact PII from logs: `User ***@example.com submitted form`
- Test with synthetic data only
- Encrypt sensitive exports if storing locally
- Delete exported data after use
- Document why PII access is needed for any feature

## Code Review Checklist

Before committing code that touches user data:

- [ ] No PII in console.log statements
- [ ] No PII in error messages
- [ ] No real user data in test files
- [ ] No PII in git commit messages
- [ ] Placeholder data used in documentation
- [ ] Data access is minimal and justified

## Testing with PII

```javascript
// ✅ GOOD - Synthetic test data
const testUser = {
  name: 'Test User',
  email: 'test@example.com'
};

// ❌ BAD - Real user data
const testUser = {
  name: 'John Smith',
  email: 'john.smith@gmail.com'
};
```

## Logging

```javascript
// ✅ GOOD - Redacted logging
console.log(`Form submitted for user ${userId}`);
console.log(`Email domain: ${email.split('@')[1]}`);

// ❌ BAD - PII in logs
console.log(`Form submitted for ${name} (${email})`);
```

## Incident Response

If PII is accidentally exposed (committed to git, logged, shared):

1. **Immediate Action**: Remove/redact the exposure immediately
2. **Git History**: Use `git filter-branch` or BFG Repo-Cleaner to remove from history
3. **Notification**: Inform the project owner immediately
4. **Documentation**: Document what happened and how it was resolved
5. **Prevention**: Update processes to prevent recurrence

## Summary

**Treat user data with the utmost respect and care. When in doubt, ask before accessing, logging, or sharing any PII.**

