# DigitalOcean App Platform - Quick Start Guide

## Prerequisites
- A DigitalOcean account
- Your code pushed to a GitHub repository
- GitHub connected to your DigitalOcean account

## Step-by-Step Deployment

### 1. Create PostgreSQL Database (5 minutes)

1. Go to [DigitalOcean Databases](https://cloud.digitalocean.com/databases)
2. Click **"Create Database Cluster"**
3. Choose:
   - **Database Engine**: PostgreSQL
   - **Version**: 16
   - **Datacenter Region**: Choose closest to your users (e.g., New York, San Francisco, Amsterdam)
   - **Database Plan**: Start with Basic ($15/month) or Dev ($12/month for testing)
4. Click **"Create Database Cluster"**
5. Wait for it to provision (2-3 minutes)
6. Once ready, note the **Connection String** (you'll need this later)

### 2. Deploy the Application (10 minutes)

#### Option A: Using App Spec (Easiest)

1. Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
2. Click **"Create App"**
3. Select **"GitHub"** as source
4. Authorize DigitalOcean to access your repository
5. Select your **MedicaLLM repository**
6. Select the **branch** (usually `main` or `master`)
7. Click **"Next"**
8. On the "Resources" page, click **"Edit App Spec"**
9. **Delete everything** in the editor
10. **Copy and paste** the entire contents of `.do/app.yaml` from your repository
11. **Update the following lines** in the spec:
    ```yaml
    github:
      branch: main  # Change to your actual branch name
    ```
12. Click **"Save"**
13. Click **"Next"**

#### Option B: Manual Configuration (Alternative)

If you prefer to configure manually:

1. Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
2. Click **"Create App"**
3. Select your repository and branch
4. DigitalOcean will try to auto-detect components (it will fail - that's expected)
5. Click **"Edit Plan"** and manually add:

**Backend Service:**
- Click **"Add Component"** → **"Web Service"**
- Name: `backend`
- Source Directory: `/backend`
- Dockerfile Path: `backend/Dockerfile`
- HTTP Port: `8000`
- HTTP Request Routes: `/api`
- Health Check: HTTP, Path: `/health`

**Frontend Service:**
- Click **"Add Component"** → **"Web Service"**
- Name: `frontend`
- Source Directory: `/frontend`
- Dockerfile Path: `frontend/Dockerfile.appplatform`
- HTTP Port: `80`
- HTTP Request Routes: `/`

### 3. Configure Environment Variables (5 minutes)

On the Environment Variables page, add these:

#### Required Variables (Backend):

```
JWT_SECRET = <generate-random-string>  [Encrypted]
ADMIN_PASSWORD = <your-admin-password>  [Encrypted]
DO_POSTGRES_URL = <your-database-connection-string>  [Encrypted]
```

**How to generate JWT_SECRET:**
- Run in terminal: `openssl rand -hex 32`
- Or use: https://generate-secret.vercel.app/32

#### Optional but Recommended:

```
DO_MODEL_ACCESS_KEY = <your-digitalocean-api-key>  [Encrypted]
HF_TOKEN = <your-huggingface-token>  [Encrypted]
SCOPUS_API_KEY = <your-scopus-key>  [Encrypted]
NCBI_API_KEY = <your-ncbi-key>  [Encrypted]
OPENALEX_EMAIL = <your-email>  [Encrypted]
```

#### Default Values (Already set in app.yaml):
- `DO_LLM_MODEL_ID`: openai-gpt-oss-120b
- `HF_EMBEDDING_MODEL_ID`: nomic-ai/nomic-embed-text-v1
- `LOG_LEVEL`: INFO
- `ADMIN_USERNAME`: medicallm
- `VITE_USE_HTTPS`: true

### 4. Launch the App

1. Review your configuration
2. Click **"Create Resources"**
3. Wait for the build (5-10 minutes for first deployment)
4. Monitor the build logs for any errors

### 5. Initialize the Database (2 minutes)

Once the app is deployed:

1. Go to your app in the DigitalOcean dashboard
2. Click on the **backend** component
3. Click **"Console"** tab
4. Run these commands:
   ```bash
   python scripts/init_tables.py
   python scripts/seed.py
   ```

### 6. Access Your Application

Your app will be available at:
```
https://your-app-name-xxxxx.ondigitalocean.app
```

- **Frontend**: `https://your-app-name-xxxxx.ondigitalocean.app/`
- **Backend API**: `https://your-app-name-xxxxx.ondigitalocean.app/api/`
- **Health Check**: `https://your-app-name-xxxxx.ondigitalocean.app/api/health`

## Troubleshooting

### "No components detected" Error
✅ **Solution**: Use the App Spec method (Option A above). The auto-detection doesn't work because your app has subdirectories.

### Build Fails with "Python version" Error
✅ **Solution**: The app requires Python >= 3.11. This should work automatically with the Dockerfile.

### Frontend Shows "Cannot connect to backend"
✅ **Solution**: 
- Check that both services are running (green status)
- Verify backend health check passes: `/api/health`
- Check browser console for CORS errors
- Ensure `CORS_ALLOWED_ORIGINS` includes your app URL

### Database Connection Fails
✅ **Solution**:
- Verify `DO_POSTGRES_URL` is correctly set
- Check database is in "Available" state
- Ensure database and app are in the same region (recommended)
- Check database firewall allows App Platform connections

### App Crashes After Deployment
✅ **Solution**:
- Check runtime logs in the DigitalOcean dashboard
- Verify all required environment variables are set
- Check that database is accessible
- Look for missing API keys in logs

## Cost Estimate

**Minimum Setup:**
- Backend: Basic (512MB RAM) - $5/month
- Frontend: Basic (512MB RAM) - $5/month
- Database: Dev Database - $12/month
- **Total: ~$22/month**

**Production Setup:**
- Backend: Professional (1GB RAM) - $12/month
- Frontend: Basic (512MB RAM) - $5/month
- Database: Basic Database - $15/month
- **Total: ~$32/month**

## Next Steps

1. **Custom Domain**: Add your own domain in App Settings
2. **Monitoring**: Set up alerts for health check failures
3. **Scaling**: Increase instance count or size as needed
4. **Backups**: Enable daily database backups
5. **CI/CD**: Enable auto-deploy on push to your branch

## Getting Help

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [DigitalOcean Community](https://www.digitalocean.com/community)
- Check your application logs in the DigitalOcean dashboard
