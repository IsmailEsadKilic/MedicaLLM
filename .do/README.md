# DigitalOcean Deployment Configuration

This folder contains configuration files for deploying MedicaLLM to DigitalOcean App Platform.

## Files

### `app.yaml`
Full-featured App Spec with all configuration options including database provisioning.

**Use this if:**
- You want DigitalOcean to create and manage the database for you
- You need all optional services configured
- You want a complete production setup

### `app-simple.yaml`
Simplified App Spec with minimal configuration and clear comments.

**Use this if:**
- You're deploying for the first time
- You want to understand the configuration better
- You prefer to create the database manually
- You want to start simple and add features later

## How to Use

1. **Choose your App Spec file** (`app.yaml` or `app-simple.yaml`)

2. **Update the configuration:**
   - Change `region` to your preferred datacenter
   - Update `github.branch` if not using `main`
   - Adjust `instance_size_slug` based on your needs

3. **Deploy:**
   - Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Select your repository
   - Click "Edit App Spec"
   - Paste the contents of your chosen file
   - Click "Save" and continue

4. **Set environment variables** in the DigitalOcean UI (see DIGITALOCEAN_QUICKSTART.md)

## Instance Sizes

| Size | RAM | vCPU | Price/month |
|------|-----|------|-------------|
| basic-xxs | 512MB | 0.5 | $5 |
| basic-xs | 1GB | 1 | $12 |
| basic-s | 2GB | 1 | $24 |
| basic-m | 4GB | 2 | $48 |

## Regions

- `nyc` - New York (USA)
- `sfo` - San Francisco (USA)
- `ams` - Amsterdam (Netherlands)
- `sgp` - Singapore
- `fra` - Frankfurt (Germany)
- `lon` - London (UK)
- `blr` - Bangalore (India)
- `syd` - Sydney (Australia)

## Need Help?

See the main deployment guides:
- `../DIGITALOCEAN_QUICKSTART.md` - Step-by-step deployment guide
- `../DEPLOYMENT.md` - Comprehensive deployment documentation
