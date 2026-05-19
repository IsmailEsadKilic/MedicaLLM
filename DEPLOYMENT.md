# DigitalOcean Deployment Guide

## Option 1: Using App Spec (Recommended)

1. **Create a Managed PostgreSQL Database**
   - Go to DigitalOcean Dashboard → Databases
   - Create a new PostgreSQL 16 database
   - Note the connection string

2. **Deploy Using App Spec**
   - Go to DigitalOcean Dashboard → Apps
   - Click "Create App"
   - Select your GitHub repository
   - Choose "Edit App Spec" and paste the contents of `.do/app.yaml`
   - Update the following in the App Spec:
     - Change `github.branch` to your actual branch name (e.g., `main` or `master`)
     - Update `region` if needed (e.g., `nyc`, `sfo`, `ams`)
   - Click "Next" and configure environment variables

3. **Set Environment Variables**
   In the DigitalOcean App Platform UI, set these as encrypted variables:
   - `JWT_SECRET` - Generate a secure random string
   - `DO_MODEL_ACCESS_KEY` - Your DigitalOcean API key for AI models
   - `ADMIN_PASSWORD` - Admin user password
   - `SCOPUS_API_KEY` - (Optional) Scopus API key
   - `OPENALEX_EMAIL` - (Optional) Your email for OpenAlex
   - `HF_TOKEN` - (Optional) HuggingFace token
   - `NCBI_API_KEY` - (Optional) NCBI API key

4. **Deploy**
   - Click "Create Resources"
   - Wait for the build and deployment to complete

## Option 2: Manual Component Configuration

If you prefer to configure manually in the UI:

### Backend Service
- **Type**: Web Service
- **Source Directory**: `/backend`
- **Dockerfile Path**: `backend/Dockerfile`
- **HTTP Port**: 8000
- **HTTP Routes**: `/api`
- **Health Check Path**: `/health`
- **Environment Variables**: (Same as above)

### Frontend Service
- **Type**: Static Site or Web Service
- **Source Directory**: `/frontend`
- **Dockerfile Path**: `frontend/Dockerfile`
- **HTTP Port**: 80
- **HTTP Routes**: `/`
- **Build-time Environment Variables**:
  - `VITE_USE_HTTPS=true`

### Database
- **Type**: PostgreSQL
- **Version**: 16
- **Plan**: Choose based on your needs (Basic or Professional)

## Option 3: Using Docker Compose (Alternative)

If you want to deploy to a DigitalOcean Droplet instead:

1. Create a Droplet with Docker pre-installed
2. SSH into the droplet
3. Clone your repository
4. Copy `.env.example` to `.env` and configure
5. Run: `docker compose up -d`

## Post-Deployment Steps

1. **Initialize Database**
   - SSH into the backend container or use the console
   - Run: `python scripts/init_tables.py`
   - Run: `python scripts/seed.py` (if needed)

2. **Verify Deployment**
   - Check backend health: `https://your-app.ondigitalocean.app/api/health`
   - Access frontend: `https://your-app.ondigitalocean.app/`

3. **Configure CORS**
   - The `CORS_ALLOWED_ORIGINS` is automatically set to `${APP_URL}`
   - If you have a custom domain, update this variable

## Troubleshooting

### "No components detected" Error
- Make sure you're using the App Spec (`.do/app.yaml`)
- Verify that `source_dir` paths are correct
- Check that Dockerfiles exist in the specified paths

### Build Failures
- Check build logs in the DigitalOcean dashboard
- Verify all required environment variables are set
- Ensure Python version compatibility (requires Python >= 3.11)

### Database Connection Issues
- Verify `DO_POSTGRES_URL` is correctly set
- Check database firewall rules (should allow App Platform)
- Ensure database is in the same region as your app

### Frontend Can't Connect to Backend
- Verify the backend route is set to `/api`
- Check that CORS is properly configured
- Ensure frontend is using HTTPS in production

## Scaling

To scale your application:
- Increase instance count for backend/frontend
- Upgrade instance size (basic-xs → basic-s → basic-m)
- Upgrade database plan for better performance

## Monitoring

- Use DigitalOcean's built-in monitoring
- Check application logs in the dashboard
- Set up alerts for health check failures
