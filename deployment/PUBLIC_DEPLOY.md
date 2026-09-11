# Global / public deployment (Render)

Agent 66 is packaged as **one HTTPS service**: FastAPI serves the API and the built React app from the same origin (so `/api` works without a separate CORS setup).

## Deploy on Render (public URL)

1. Push this repository to GitHub (already linked as `origin`).
2. Open [Render Blueprint](https://dashboard.render.com/select-repo?type=blueprint) and connect `Counsellor-supporting-agent`.
3. Apply `render.yaml`.
4. In the Render dashboard, set these **secret** env vars (do not commit them):
   - `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`
   - `EMAIL_ADMIN`
   - `GEMINI_API_KEY` (if used)
   - After the first deploy, set:
     - `PUBLIC_BASE_URL=https://YOUR-SERVICE.onrender.com`
     - `APP_LOGIN_URL=https://YOUR-SERVICE.onrender.com/login`
5. Wait for the build. Open `https://YOUR-SERVICE.onrender.com/health` then `/login`.

## Notes

- Free Render services **sleep when idle** and can take ~1 minute to wake.
- The encrypted SQLite file on the free plan is **ephemeral** unless you add a paid persistent disk. Redeploys can wipe local DB data.
- Never commit `.env` or database files.
