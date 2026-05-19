# MedicaLLM — DigitalOcean Droplet Deployment

End-to-end production deployment to a single DigitalOcean droplet using the
existing Docker Compose setup. The frontend nginx terminates TLS on 80/443
and reverse-proxies `/api/` to the backend over an internal Docker network,
so only the frontend is exposed publicly.

---

## What runs where

```
            ┌────────────────────  Public Internet  ────────────────────┐
            │                                                            │
            │           https://your-domain.com  (443)                   │
            │                       │                                    │
            └───────────────────────┼────────────────────────────────────┘
                                    ▼
       ┌──────────────────────────────────────────────────────────┐
       │  Droplet (Ubuntu 22.04+ / Docker)                        │
       │                                                          │
       │   frontend (nginx:alpine) ──────► backend (uvicorn)      │
       │     • serves React SPA           • FastAPI on :8000      │
       │     • TLS via Let's Encrypt      • talks to DO Postgres  │
       │     • proxies /api/ → backend    • ChromaDB (local vol)  │
       │     • ports 80, 443 public       • not publicly exposed  │
       │                                                          │
       │   certbot (sidecar) ─── auto-renews certs every 12h      │
       └──────────────────────────────────────────────────────────┘
```

Database stays where it is (DigitalOcean Managed Postgres). The droplet is
stateful only for the ChromaDB vector store and PDF cache, which live in
named Docker volumes.

---

## 1. Provision the droplet

1. Create a droplet:
   - **Image:** Ubuntu 22.04 LTS (or 24.04)
   - **Plan:** Regular Intel **4 GB RAM / 2 vCPU** minimum
     (the embedding model needs the headroom; 2 GB will OOM on first warmup).
   - **Datacenter:** same region as your Managed Postgres (for low DB latency).
   - **Auth:** add your SSH key.
   - **Firewall:** allow `22`, `80`, `443` only.
2. Point your domain's **A record** at the droplet's public IPv4. Wait until
   `dig +short your-domain.com` returns the droplet IP before continuing.

## 2. Install Docker

```bash
ssh root@<droplet-ip>

apt-get update && apt-get -y upgrade
apt-get -y install ca-certificates curl gnupg git ufw

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  | tee /etc/apt/sources.list.d/docker.list

apt-get update
apt-get -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Firewall
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable

docker compose version  # sanity check
```

## 3. Pull the project

```bash
mkdir -p /opt && cd /opt
git clone <your-repo-url> medicallm
cd medicallm
```

> Don't have a remote yet? `scp -r ./MedicaLLM-master root@<droplet-ip>:/opt/medicallm`
> works for a one-shot bootstrap.

## 4. Configure production env

```bash
cp .env.production.example .env
chmod 600 .env
nano .env
```

Fill in **at minimum**:

| Variable | What it is |
|----------|------------|
| `DOMAIN_NAME` | The public domain you mapped to the droplet (no protocol). |
| `LETSENCRYPT_EMAIL` | Used by Certbot for expiry notices. |
| `JWT_SECRET` | `openssl rand -base64 48` |
| `ADMIN_PASSWORD` | Strong password for the admin panel. |
| `DO_POSTGRES_URL` | DigitalOcean Managed Postgres URL (`?sslmode=require`). |
| `DO_MODEL_ACCESS_KEY` | DigitalOcean AI inference key. |
| `CORS_ALLOWED_ORIGINS` | `https://your-domain.com` (must match `DOMAIN_NAME`). |

Also add the droplet's public IP to your DigitalOcean Postgres
**Trusted Sources** so the database accepts connections from it.

## 5. Bootstrap TLS + bring the stack up

The repo ships a script that handles the Let's Encrypt chicken-and-egg
problem (nginx needs a cert to start, certbot needs nginx to issue one):

```bash
bash scripts/init-letsencrypt.sh
```

What it does:
1. Drops a 1-day self-signed cert so nginx can boot.
2. Builds and starts the `frontend` and `backend` containers.
3. Replaces the dummy cert with a real one via certbot's HTTP-01 challenge.
4. Reloads nginx and starts the certbot renewal sidecar.

Visit `https://your-domain.com` — the SPA loads, `/api/health` returns 200,
and the cert is valid.

## 6. Day-to-day operations

```bash
# Tail logs
docker compose -f compose.yml -f compose.prod.yml logs -f backend
docker compose -f compose.yml -f compose.prod.yml logs -f frontend

# Restart a single service
docker compose -f compose.yml -f compose.prod.yml restart backend

# Pull new code and redeploy (cert + data are preserved)
cd /opt/medicallm
git pull
docker compose -f compose.yml -f compose.prod.yml up -d --build

# Stop everything
docker compose -f compose.yml -f compose.prod.yml down

# WIPE everything including ChromaDB and PDFs (irreversible)
docker compose -f compose.yml -f compose.prod.yml down -v
```

### Backups

ChromaDB and the PDF cache live in Docker named volumes. Snapshot them
periodically:

```bash
docker run --rm \
  -v medicallm-master_chromadb-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/chromadb-$(date +%F).tar.gz -C /data .
```

Postgres is managed by DigitalOcean — enable automatic backups from the DO
console; nothing to do on the droplet.

### Cert renewal

The `certbot` sidecar runs `certbot renew` every 12 hours. Renewal happens
automatically inside the 30-day window. Force a test renewal with:

```bash
docker compose -f compose.yml -f compose.prod.yml exec certbot \
  certbot renew --dry-run
```

---

## How frontend ↔ backend talk

* In **prod**, the React app is a static bundle served by nginx. The Vite
  build was done with `VITE_USE_HTTPS=true` and **no** `VITE_BACKEND_URL`,
  so all `fetch('/api/...')` calls are **same-origin relative** — they hit
  the same nginx, which proxies them over the internal Docker network to
  `http://backend:8000` (see `frontend/nginx-ssl.conf.template`).
* The backend never needs to be exposed to the public internet, and the
  browser never sees a different origin, so the only CORS entry needed is
  `https://${DOMAIN_NAME}`.
* The streaming endpoint (`/api/agent/query-stream`) uses SSE; the nginx
  config disables `proxy_buffering` for `/api/` so chunks flush in real time.

## Troubleshooting

* **`502 Bad Gateway` on `/api/`** → backend is unhealthy. Check
  `docker compose ... logs backend`. Most common cause: bad
  `DO_POSTGRES_URL` or droplet IP not added to DO Postgres trusted sources.
* **Cert request fails with `Connection refused`** → DNS not yet pointing at
  the droplet, or port 80 is firewalled. Verify with
  `dig +short $DOMAIN_NAME` and `ufw status`.
* **Frontend builds but shows blank page** → open the browser console.
  If it says `Mixed Content`, you forgot `VITE_USE_HTTPS=true`; rebuild with
  `docker compose -f compose.yml -f compose.prod.yml build --no-cache frontend`.
* **Embedding warmup OOM-kills the backend** → bump the droplet to 4 GB RAM
  (the `nomic-embed-text-v1` model needs ~1.5 GB resident).
