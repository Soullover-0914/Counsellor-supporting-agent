# Global / public deployment (Render)

Agent 66 ships as **one HTTPS service**: FastAPI serves the API and the built React app from the same origin.

## Why data disappeared before

Free / ephemeral container disks reset on every redeploy. The encrypted SQLite file must live on a **Render Persistent Disk** at `/var/data`.

## Deploy steps

1. Push `main` (includes `Dockerfile` + `render.yaml`).
2. Open [Render Blueprint](https://dashboard.render.com/select-repo?type=blueprint).
3. Blueprint name: `agent66` · Branch: `main` · Path: `render.yaml`.
4. Confirm service plan is **Starter** (or higher) so the **1GB disk** at `/var/data` is created.
5. Set secrets in the dashboard (see below).
6. Deploy and wait for healthy status.
7. Open `https://YOUR-SERVICE.onrender.com/health` — expect `storage_path` `/var/data`.
8. Open `/login` and sign in (`admin001` / `admin123` after first-boot seed).

### If the service already exists on Free plan

1. In Render → **agent66-counselling** → **Settings**
2. Upgrade instance to **Starter**
3. Add **Persistent Disk**: mount `/var/data`, size 1GB
4. Ensure env `DATABASE_PATH=/var/data/counselling_agent_encrypted.db`
5. **Do not rotate** `DATABASE_ENCRYPTION_KEY` if you need to keep an existing file
6. Manual Deploy

First boot on an empty disk seeds demo users + sample referrals/resources/records once. Later redeploys preserve `/var/data`.

## Required environment variables

| Key | Notes |
|-----|--------|
| `ENVIRONMENT` | `production` |
| `AUTH_SECRET_KEY` | Generate once; keep forever |
| `DATABASE_ENCRYPTION_KEY` | Generate once; keep forever |
| `DATABASE_PATH` | `/var/data/counselling_agent_encrypted.db` |
| `FRONTEND_DIST` | `/app/frontend/dist` |
| `SEED_DEMO_USERS` | `true` (first boot only; skips when users exist) |
| `APP_LOGIN_URL` | `https://YOUR-SERVICE.onrender.com/login` |
| `PUBLIC_BASE_URL` | `https://YOUR-SERVICE.onrender.com` |
| `SMTP_HOST` | e.g. `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | sender account |
| `SMTP_PASSWORD` | app password |
| `SMTP_FROM_EMAIL` | from address |
| `SMTP_FROM_NAME` | `Agent 66` |
| `SMTP_USE_TLS` | `true` |
| `EMAIL_ADMIN` | admin notification inbox |
| `GEMINI_API_KEY` | optional |

## Redeploy safety

- Redeploys rebuild the Docker image but **must remount the same disk**.
- Changing `DATABASE_ENCRYPTION_KEY` makes the existing DB unreadable.
- First-boot seed does **not** run again when users already exist.

## Smoke test

```powershell
$env:BASE_URL="https://YOUR-SERVICE.onrender.com"
cd backend
.\.venv\Scripts\python.exe test_deploy_persistence.py
```
