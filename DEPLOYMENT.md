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


---

## CI/CD: automatic deploys from GitHub

Every push to `main` triggers `.github/workflows/deploy.yml`, which SSHes
into the droplet and runs the same `git pull && docker compose up -d --build`
you'd run by hand. The workflow includes:

* a 30-second cancel window before any change touches the droplet,
* a 5-attempt post-deploy health probe (looks for `"status":"ok"` JSON, not
  just HTTP 200),
* automatic rollback to the previous commit if verification fails,
* Resend email notifications on success and on failure.

### One-time setup

1. **SSH key for GitHub → droplet**

   On your laptop (or any local machine):

   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/medicallm_deploy -N ""
   ssh-copy-id -i ~/.ssh/medicallm_deploy.pub root@<droplet-ip>
   # verify
   ssh -i ~/.ssh/medicallm_deploy root@<droplet-ip> "echo deploy-key works"
   ```

2. **GitHub Secrets** (`Settings → Secrets and variables → Actions`)

   | Secret | Value |
   |---|---|
   | `SSH_PRIVATE_KEY` | Contents of `~/.ssh/medicallm_deploy` (the **private** key, no passphrase). |
   | `DROPLET_HOST` | Droplet's public IP or DNS name. |
   | `DROPLET_USER` | `root` (or whichever user owns `/opt/medicallm`). |
   | `RESEND_API_KEY` | Same key already used for verification emails. |
   | `ALERT_RECIPIENTS` | Comma-separated emails that should receive deploy notifications. |
   | `RESEND_FROM_ADDRESS` | Optional override; defaults to `MedicaLLM Deploys <noreply@medicallm.com.tr>`. |

3. **GitHub Environment** (`Settings → Environments → New environment → production`)

   The workflow targets the `production` environment so deploy history shows
   up under the repo's "Deployments" panel. No protection rules required for
   solo dev; add reviewers later if the team grows.

### Day-to-day

* **Push to `main`** → automatic deploy. Watch progress in `Actions` tab.
* **Skip deploy for a commit** → put `[skip-deploy]` in the commit message.
* **Manual re-run** → `Actions → Deploy to production → Run workflow → main`.
* **What's currently live?** → `https://medicallm.com.tr/api/version` returns
  `{ "commit": "<sha>", "branch": "main", "deployed_at": "<UTC>" }`.

### Rollback

The deploy workflow handles failures automatically — the droplet keeps the
previous SHA at `/tmp/medicallm-rollback-target` and reverts on a failed
health check. For a manual rollback (e.g. a bug that gets past the probe):

```bash
git revert HEAD
git push origin main   # triggers a fresh deploy of the revert commit
```

Or, in an emergency, on the droplet:

```bash
cd /opt/medicallm
git log --oneline -10
git reset --hard <previous-sha>
docker compose -f compose.yml -f compose.prod.yml up -d --build
```

### Monitoring

`.github/workflows/health-monitor.yml` runs every 5 minutes against
`/health`. Three consecutive failures (~15 minutes of real downtime) trigger
a Resend email; the next successful probe sends a recovery email. State is
persisted via `actions/cache` so consecutive runs share a counter.



---

## Branch protection (recommended)

Once the team grows past one person, lock down `main` so a hasty push can't
go straight to production. The CI workflow we ship is exactly the
green/red signal a protection rule needs to gate on.

### One-time setup

1. **Settings → Branches → Add rule** (or **Add classic branch protection**)
2. **Branch name pattern:** `main`
3. Enable:
   - **Require a pull request before merging**
     - **Require approvals:** 1 (raise once you have more reviewers)
     - **Dismiss stale pull request approvals when new commits are pushed**
   - **Require status checks to pass before merging**
     - **Require branches to be up to date before merging**
     - Status checks to require:
       - `Backend tests` (from `ci.yml`)
       - `Frontend tests + build` (from `ci.yml`)
   - **Require conversation resolution before merging**
   - **Do not allow bypassing the above settings** (covers admins too —
     turn off temporarily if you ever need an emergency unlock)
4. Leave the rest off unless you specifically want them.

### Result

* `main` is read-only outside PRs.
* Every PR must have green CI and one approval before the merge button
  unlocks.
* The deploy workflow still runs the moment a PR is merged — protection
  doesn't slow shipping, it just enforces the path.

### Emergency bypass

If a critical fix needs to skip review (production is broken right now):

1. Pop the protection rule from `Settings → Branches`.
2. Push the fix.
3. Re-enable protection.

Document the reason in the next standup; emergency bypasses should be rare.

---

## Notification policy

The deploy workflow does NOT email on every push. Mail is sent when:

- The deploy fails and the rollback runs (always — needs immediate attention).
- The deploy is triggered manually via `workflow_dispatch` (deliberate; you
  asked for a receipt).
- The deploy lands on a Saturday or Sunday (weekend = quieter on-call;
  louder signal helps).
- The deploy lands outside business hours UTC (before 06:00 or after 18:00).

Routine weekday merges run silently — the green check on the Actions
page is the receipt. Adjust the day/hour thresholds in
`.github/workflows/deploy.yml` if the rhythm doesn't match yours.

