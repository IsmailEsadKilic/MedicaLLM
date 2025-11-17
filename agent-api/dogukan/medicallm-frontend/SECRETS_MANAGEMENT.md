# 🔐 Secrets Management Guide

## Overview

Secrets are sensitive data like API keys, database passwords, and OAuth credentials. **NEVER** commit them to Git!

---

## 📁 Environment Files Hierarchy

Next.js loads environment variables in this order (later ones override earlier):

```
1. .env                    # Committed, shared defaults
2. .env.local              # NOT committed, local overrides
3. .env.development        # Committed, development defaults
4. .env.development.local  # NOT committed, local dev overrides
5. .env.production         # Committed, production defaults
6. .env.production.local   # NOT committed, local prod overrides
```

### What to Commit vs Not Commit:

✅ **COMMIT:**
- `.env` (non-sensitive defaults)
- `.env.development` (non-sensitive dev settings)
- `.env.production` (non-sensitive prod settings)
- `.env.example` (template for team)

❌ **NEVER COMMIT:**
- `.env.local` (all your secrets go here)
- `.env*.local` (any local files)
- Actual API keys, passwords, tokens

---

## 🛠️ Setup for MedicaLLM

### Step 1: Create Environment Files

#### `.env.example` (Template for team)
```env
# NextAuth Configuration
AUTH_SECRET=generate-with-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000

# OAuth Providers
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Database (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/medicallm
```

#### `.env.local` (Your actual secrets - NOT committed)
```env
AUTH_SECRET=FqldpGWjiuvZ5HFsET7oZpxm9RNe3swv5RdFWYb3Vyo=
NEXTAUTH_URL=http://localhost:3000
GOOGLE_CLIENT_ID=123456789.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-actual-secret
OPENAI_API_KEY=sk-proj-actual-key-here
```

---

## 🔒 Security Best Practices

### 1. Generate Strong Secrets

```bash
# For AUTH_SECRET (32 bytes)
openssl rand -base64 32

# Or with Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"

# For database passwords (64 chars)
openssl rand -base64 48
```

### 2. Variable Naming Conventions

Next.js has two types of env vars:

#### Server-Side Only (Private)
```env
# These are ONLY available in API routes and server components
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
AUTH_SECRET=...
```

#### Client-Side Exposed (Public)
```env
# Must prefix with NEXT_PUBLIC_ to expose to browser
NEXT_PUBLIC_API_URL=https://api.medicallm.com
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
```

⚠️ **WARNING:** Never put secrets in `NEXT_PUBLIC_*` variables!

### 3. Validation

Add runtime validation in your code:

```typescript
// lib/env.ts
export function validateEnv() {
  const required = [
    'AUTH_SECRET',
    'GOOGLE_CLIENT_ID',
    'GOOGLE_CLIENT_SECRET',
  ];

  const missing = required.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(', ')}`
    );
  }
}
```

---

## 🚀 Production Deployment

### Vercel (Recommended for Next.js)

1. Go to your project settings on Vercel
2. Navigate to "Environment Variables"
3. Add each variable:
   - Key: `AUTH_SECRET`
   - Value: `[your-secret]`
   - Environment: Production, Preview, Development
4. Redeploy your app

### Other Platforms

#### Railway
```bash
railway variables set AUTH_SECRET=your-secret
```

#### Heroku
```bash
heroku config:set AUTH_SECRET=your-secret
```

#### Docker
```yaml
# docker-compose.yml
services:
  app:
    environment:
      - AUTH_SECRET=${AUTH_SECRET}
    env_file:
      - .env.local
```

#### AWS / Azure / GCP
Use their secret management services:
- AWS: Secrets Manager / Parameter Store
- Azure: Key Vault
- GCP: Secret Manager

---

## 🔄 Rotating Secrets

**When to rotate:**
- Suspected compromise
- Team member leaves
- Regular schedule (every 90 days)

**How to rotate:**

1. Generate new secret:
   ```bash
   openssl rand -base64 32
   ```

2. Update `.env.local` locally
3. Update production environment variables
4. Restart your app
5. Invalidate old sessions (for AUTH_SECRET)

---

## 👥 Team Collaboration

### Sharing Secrets Securely

❌ **NEVER:**
- Commit to Git
- Send via Slack/Email/SMS
- Share in screenshots

✅ **USE:**
- **1Password** / **LastPass** (password managers)
- **Doppler** / **Infisical** (secret management platforms)
- **HashiCorp Vault** (enterprise)
- Encrypted files with PGP/GPG

### Onboarding New Developer

1. Share `.env.example` via Git
2. Send actual secrets via secure channel
3. They create their own `.env.local`

---

## 📋 Checklist for MedicaLLM

- [ ] `.env.local` created with all secrets
- [ ] `.env.example` created (no actual secrets)
- [ ] `.gitignore` includes `.env*.local`
- [ ] Production secrets added to hosting platform
- [ ] AUTH_SECRET is strong (32+ bytes)
- [ ] No `NEXT_PUBLIC_` prefix on sensitive data
- [ ] Team knows how to securely get secrets
- [ ] Rotation schedule established

---

## 🐛 Troubleshooting

### "MissingSecret" Error
- Check `.env.local` exists in project root
- Verify variable names match exactly (case-sensitive)
- Restart dev server after changes

### Variables Not Loading
```bash
# Restart the server
# Press Ctrl+C, then:
npm run dev

# Or clear Next.js cache:
rm -rf .next
npm run dev
```

### Production Variables Not Working
- Check hosting platform environment variables
- Verify correct environment selected (production/preview)
- Redeploy after adding variables

---

## 📚 Additional Resources

- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
- [NextAuth.js Environment Variables](https://authjs.dev/guides/environment-variables)
- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

## 🎯 Quick Reference

| Variable | Type | Where | Purpose |
|----------|------|-------|---------|
| `AUTH_SECRET` | Server | `.env.local` | Encrypts session tokens |
| `GOOGLE_CLIENT_ID` | Server | `.env.local` | OAuth identification |
| `GOOGLE_CLIENT_SECRET` | Server | `.env.local` | OAuth secret |
| `OPENAI_API_KEY` | Server | `.env.local` | AI API access |
| `NEXTAUTH_URL` | Server | `.env.local` | Base URL for auth |
| `NEXT_PUBLIC_*` | Client | `.env.local` | Exposed to browser |

**Remember:** When in doubt, keep it secret! 🤫

