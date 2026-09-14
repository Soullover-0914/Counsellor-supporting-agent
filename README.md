# Agent 66 — Counselling Support System

Institutional counselling-support routing platform (not a therapy product).

## Stack

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + JWT RBAC
- **Database:** SQLCipher encrypted SQLite
- **Deploy:** Docker on Render (single same-origin service)

## Local development

```powershell
# Backend
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

- Frontend API base (dev): `http://127.0.0.1:8000`
- Separate Vercel production frontend uses `VITE_API_BASE_URL=https://agent66-counselling.onrender.com`
- Production API base on Render (same-origin SPA): `/api`

Copy `deployment/.env.example` patterns into `backend/.env`. Never commit secrets.

Email is sent by the backend through **Brevo** (`BREVO_API_KEY` and `BREVO_FROM_EMAIL` in server environment only). The frontend never talks to Brevo.

When the Vercel frontend calls the Render API, set `CORS_ALLOWED_ORIGINS` on the backend to the exact frontend origins (comma-separated, no trailing slash). Example: `http://127.0.0.1:5173,http://localhost:5173,https://frontend-pi-fawn-59ukp6dnl5.vercel.app`.

## Public deployment (Render)

See `deployment/PUBLIC_DEPLOY.md` and `deployment/DEPLOYMENT_CHECKLIST.md`.

Critical production requirements:

1. **Persistent Disk** mounted at `/var/data` (1GB+)
2. `DATABASE_PATH=/var/data/counselling_agent_encrypted.db`
3. Stable `DATABASE_ENCRYPTION_KEY` and `AUTH_SECRET_KEY` across redeploys
4. `SEED_DEMO_USERS=true` only for first-boot demo data (never overwrites existing DB)

## Demo logins (first-boot seed only)

| Username | Password | Role |
|----------|----------|------|
| admin001 | admin123 | admin |
| hod001 | hod123 | hod |
| counsellor001 | counsellor123 | counsellor |
| student001 | student123 | student |

## Signup / approval email flow

Student signup → pending registration → admin notified → admin approves → temporary password emailed → one-time password change. Temporary passwords are never shown in the admin UI.
