# 🗄️ DynamoDB Local Setup Guide

## ✅ What's Been Set Up

- ✅ AWS SDK for DynamoDB installed
- ✅ DynamoDB Local package installed
- ✅ Database helper functions created
- ✅ Authentication using DynamoDB
- ✅ Auto table creation for local development

---

## 🚀 Quick Start

### Step 1: Start DynamoDB Local

**Option A: Manual (Recommended for first time)**

Open a **new terminal** and run:

```bash
npm run dynamodb:start
```

Keep this terminal open! DynamoDB Local will run on `http://localhost:8000`

**Option B: Automatic (Both together)**

In one terminal:

```bash
npm run dev:all
```

This starts both DynamoDB Local AND Next.js together!

---

### Step 2: Start Next.js (if using Option A)

In another terminal:

```bash
npm run dev
```

---

### Step 3: Test It!

1. Open http://localhost:3000
2. You'll be redirected to `/auth/signin`
3. Click "Kayıt Ol" (Sign Up)
4. Create an account
5. You'll be auto-logged in!

---

## 📁 Database Location

**Local Development:**
- DynamoDB Local runs in memory (default)
- Data is lost when you stop DynamoDB Local
- To persist data, use `--sharedDb` flag (already in script)

**Data Storage:**
- DynamoDB Local stores data in: `./dynamodb_local_db/` (created automatically)

---

## 🔧 Environment Variables

Update your `.env.local` file:

```env
# NextAuth
AUTH_SECRET=FqldpGWjiuvZ5HFsET7oZpxm9RNe3swv5RdFWYb3Vyo=
NEXTAUTH_URL=http://localhost:3000

# DynamoDB Local (Development)
USE_LOCAL_DYNAMODB=true
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
USERS_TABLE=medicallm-users

# For Production (AWS DynamoDB) - Add later
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your-key
# AWS_SECRET_ACCESS_KEY=your-secret
# USERS_TABLE=medicallm-users-prod
```

---

## 🎯 How It Works

### Local Development Flow:

```
┌─────────────────────┐
│  DynamoDB Local      │
│  (Port 8000)         │
│  In-Memory DB        │
└──────────┬───────────┘
           │
           │ AWS SDK
           │
┌──────────▼───────────┐
│  Next.js App         │
│  (Port 3000)         │
│  - Auth API          │
│  - Register API      │
│  - Chat API          │
└──────────────────────┘
```

### Production Flow (Later):

```
┌─────────────────────┐
│  AWS DynamoDB        │
│  (Cloud)             │
└──────────┬───────────┘
           │
           │ AWS SDK
           │
┌──────────▼───────────┐
│  Next.js App         │
│  (Deployed)          │
│  - Same code!        │
│  - Just different    │
│    endpoint          │
└──────────────────────┘
```

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to DynamoDB"

**Solution:**
1. Make sure DynamoDB Local is running: `npm run dynamodb:start`
2. Check if port 8000 is available
3. Wait a few seconds after starting DynamoDB Local

### Issue: "Table doesn't exist"

**Solution:**
- Table is created automatically on first registration
- If it fails, check DynamoDB Local is running
- Check console for error messages

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change port in package.json:
"dynamodb:start": "dynamodb-local --port 8001 --sharedDb"
```

### Issue: "Java not found"

**Solution:**
DynamoDB Local requires Java. Install:
- Windows: https://adoptium.net/
- Or use Docker (see below)

---

## 🐳 Alternative: Docker (No Java Needed!)

If you prefer Docker:

```bash
docker run -d -p 8000:8000 amazon/dynamodb-local
```

Then update `.env.local`:
```env
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
```

---

## 📊 Viewing Data Locally

### Option 1: AWS CLI

```bash
# Install AWS CLI first
aws dynamodb scan --table-name medicallm-users --endpoint-url http://localhost:8000
```

### Option 2: DynamoDB Admin (GUI)

```bash
npm install -g dynamodb-admin
DYNAMO_ENDPOINT=http://localhost:8000 dynamodb-admin
```

Then open http://localhost:8001

### Option 3: NoSQL Workbench

Download from AWS: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/workbench.html

---

## 🚀 Production Deployment

When deploying to production:

1. **Create DynamoDB table in AWS:**
   - Go to AWS Console → DynamoDB
   - Create table: `medicallm-users`
   - Partition key: `id` (String)
   - Add GSI: `email-index` with `email` as key

2. **Update environment variables:**
   ```env
   # Remove local settings
   # USE_LOCAL_DYNAMODB=false
   # DYNAMODB_LOCAL_ENDPOINT=...
   
   # Add AWS settings
   AWS_REGION=us-east-1
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   USERS_TABLE=medicallm-users
   ```

3. **That's it!** Same code works in production! 🎉

---

## 📋 Available Scripts

```bash
# Start DynamoDB Local only
npm run dynamodb:start

# Stop DynamoDB Local
npm run dynamodb:stop

# Start both DynamoDB + Next.js
npm run dev:all

# Start Next.js only (if DynamoDB already running)
npm run dev
```

---

## ✅ Checklist

- [ ] DynamoDB Local installed
- [ ] `.env.local` configured
- [ ] DynamoDB Local running (`npm run dynamodb:start`)
- [ ] Next.js running (`npm run dev`)
- [ ] Test registration works
- [ ] Test login works

---

## 💡 Pro Tips

1. **Keep DynamoDB Local running** in a separate terminal
2. **Use `--sharedDb` flag** to persist data between restarts
3. **Table auto-creates** on first registration - no manual setup needed!
4. **Same code** works for local and production - just change endpoint!

---

## 🆘 Need Help?

- Check terminal for error messages
- Verify DynamoDB Local is running on port 8000
- Check `.env.local` has correct settings
- Restart both services if needed

Happy coding! 🚀

