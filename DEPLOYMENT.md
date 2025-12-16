# EC2 Deployment Guide

## Changes Made

### 1. Frontend Configuration
- Updated [`frontend/src/api/config.js`](frontend/src/api/config.js) to use environment variable for API URL
- Set VITE_API_URL in docker-compose.yml to point to `http://98.80.152.122/api`

### 2. CORS Configuration
- **Backend**: Added domain and EC2 IP to allowed origins
- **Agent API**: Added domain and EC2 IP to allowed origins

### 3. Docker Compose Updates
- Changed all service ports from `ports` to `expose` (internal only)
- Added **nginx** service as reverse proxy (only port 80/443 exposed)
- Nginx routes:
  - `/` → Frontend (React app)
  - `/api/` → Backend API

### 4. Nginx Configuration
- Created `nginx/nginx.conf` with reverse proxy setup
- Includes SSL/HTTPS configuration (commented out until you have certificates)

## Deployment Steps

### 1. On Your EC2 Instance

```bash
# Clone your repository
git clone <your-repo-url>
cd MedicaLLM

# Create .env file with your AWS credentials
cat > .env << EOF
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
JWT_SECRET=<generate-a-secure-secret>
EOF

# Make sure Docker and Docker Compose are installed
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Build and start all services
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

### 2. Configure EC2 Security Group

Allow inbound traffic on:
- **Port 80** (HTTP) - from 0.0.0.0/0
- **Port 443** (HTTPS) - from 0.0.0.0/0
- **Port 22** (SSH) - from your IP only

**Do NOT expose ports 3000, 3001, 2580, or 8000 externally**

### 3. Configure Domain (Optional)

If you have a domain, add an A record:
```
Type: A
Name: @ (or subdomain)
Value: 98.80.152.122
TTL: 3600
```

Then update these files to replace `98.80.152.122` with your domain:
1. [`nginx/nginx.conf`](nginx/nginx.conf) - `server_name` line
2. [`frontend/src/api/config.js`](frontend/src/api/config.js) - Add domain to API_URL
3. [`docker-compose.yml`](docker-compose.yml) - VITE_API_URL environment variable

### 4. Enable SSL/HTTPS (Recommended)

```bash
# Install certbot on EC2
sudo yum install certbot -y

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Create SSL directory and copy certificates
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/
sudo chown -R $(whoami):$(whoami) nginx/ssl

# Uncomment SSL section in nginx/nginx.conf
# Uncomment the ssl volume mount in docker-compose.yml

# Restart nginx
docker-compose restart nginx
```

## What Stays `localhost`

✅ **Keep these as-is (internal Docker communication):**
- `DYNAMODB_ENDPOINT=http://dynamodb-local:8000`
- `AGENT_API_URL=http://agent-api:2580`
- All service names in docker-compose.yml

## What Changed to EC2 IP/Domain

✅ **Changed for external access:**
- Frontend API URL (`VITE_API_URL`)
- CORS origins in backend and agent-api
- Nginx proxy configuration

## Testing

1. **Access the application**: http://98.80.152.122
2. **Check health endpoint**: http://98.80.152.122/api/health
3. **View logs**: `docker-compose logs -f [service-name]`

## Troubleshooting

### Can't access the application
```bash
# Check if nginx is running
docker ps | grep nginx

# Check nginx logs
docker-compose logs nginx

# Test nginx config
docker exec nginx nginx -t
```

### CORS errors
- Check browser console for specific error
- Verify your domain/IP is in the CORS origins list
- Rebuild containers: `docker-compose up -d --build backend agent-api`

### Services can't communicate
- Verify all services are on the same network
- Check service names are correct in environment variables
- Use `docker-compose logs [service]` to debug

## Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or rebuild specific service
docker-compose up -d --build backend
```

## Important Notes

1. **Change JWT_SECRET** in production (don't use default)
2. **Never expose internal ports** (8000, 2580) to the internet
3. **Use HTTPS** in production (follow SSL setup above)
4. **Backup dynamodb-data** directory regularly
5. **Monitor logs** for errors: `docker-compose logs -f`
