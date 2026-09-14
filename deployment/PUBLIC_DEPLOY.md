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

## Email on Render (Brevo)

Agent 66 sends mail through **Brevo Transactional Email API** only. SMTP is not used.

1. Create a [Brevo](https://www.brevo.com/) account and verify the sender address
2. Create a transactional API key
3. In Render → Environment set:
   - `BREVO_API_KEY` (secret)
   - `BREVO_FROM_EMAIL` (verified sender)
   - `BREVO_FROM_NAME=Agent 66`
   - `EMAIL_ADMIN=...`
   - `APP_LOGIN_URL=https://YOUR-SERVICE.onrender.com/login`
   - `CORS_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,https://frontend-pi-fawn-59ukp6dnl5.vercel.app,https://agent66-counselling.onrender.com`
4. Manual Deploy
5. Approve / Resend credentials

Never commit the API key. The frontend never calls Brevo.


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
