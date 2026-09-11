# Agent 66 — Deployment Checklist

## Configuration

- [ ] `ENVIRONMENT=production`
- [ ] `AUTH_SECRET_KEY` set and **unchanged** across redeploys
- [ ] `DATABASE_ENCRYPTION_KEY` set and **unchanged** across redeploys
- [ ] `TOKEN_EXPIRY_SECONDS` verified
- [ ] Production secrets are **not** committed to source control
- [ ] `DATABASE_PATH=/var/data/counselling_agent_encrypted.db`
- [ ] `FRONTEND_DIST=/app/frontend/dist`
- [ ] `APP_LOGIN_URL=https://YOUR-SERVICE.onrender.com/login`
- [ ] `PUBLIC_BASE_URL=https://YOUR-SERVICE.onrender.com`
- [ ] SMTP vars configured (`SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `EMAIL_ADMIN`)
- [ ] `SEED_DEMO_USERS=true` for first boot only (safe: skips when users already exist)

## Persistent storage (Render)

- [ ] Web service plan supports disks (**Starter** or higher — not Free)
- [ ] Disk name `agent66-data` (or equivalent)
- [ ] Mount path `/var/data`
- [ ] Size **1GB**
- [ ] After deploy, `/health` shows `"storage_path":"/var/data"`
- [ ] After redeploy, referrals / resources / records still present

## Database

- [ ] SQLCipher database exists under `/var/data`
- [ ] Database opens with the configured encryption key
- [ ] First boot created tables + demo seed once
- [ ] Second boot / redeploy did **not** wipe data
- [ ] No plaintext DB committed to git

## Application

- [ ] Docker build succeeds
- [ ] `/health` returns healthy
- [ ] `/login` serves the React app
- [ ] `/api/v1/counselling/...` reachable same-origin
- [ ] Swagger `/docs` available if needed for ops

## Authentication / RBAC

- [ ] Valid credentials authenticate
- [ ] Invalid passwords return 401
- [ ] JWT accepted on protected routes
- [ ] Student / counsellor / mentor / faculty / HOD / dean / admin permissions verified

## Workflow

- [ ] Signup creates pending registration
- [ ] Admin receives signup email (SMTP)
- [ ] Admin approval emails temporary password to student
- [ ] One-time password change enforced
- [ ] Temporary password never shown in admin UI

## Persistence verification

- [ ] Login as `hod001` — referrals visible after first boot
- [ ] Create or note a referral id
- [ ] Trigger **Manual Deploy** / restart
- [ ] Same referral id still present
- [ ] Resources still listed
- [ ] Counselling records still listed

## Safety / governance

- [ ] Consent / crisis behaviour unchanged
- [ ] Institutional approval obtained for production use
- [ ] Named human escalation contacts verified

## Regression

- Local: `backend/test_phase19_4_8.py` (75 tests)
- Local signup flow: `backend/test_signup_password_workflow.py`
- Deploy smoke: `backend/test_deploy_persistence.py` with `BASE_URL=https://YOUR-SERVICE.onrender.com`
