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
- Production API base: same origin (`/api`)

Copy `deployment/.env.example` patterns into `backend/.env`. Never commit secrets.

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
