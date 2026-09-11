# Agent 66 Frontend

React + TypeScript + Vite client for the Agent 66 Counselling Support Agent.

## Run

1. Start the backend on `http://127.0.0.1:8000`.
2. From this directory:

```bash
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to the backend, so leave `VITE_API_BASE_URL` empty in development.

## Build

```bash
npm run build
npm run preview
```

## Notes

- Authentication tokens are stored in `sessionStorage` only for the browser tab session.
- `student_id` is read from the signed token payload when present; login responses do not include it.
- Role navigation is tailored per backend RBAC. Backend authorisation remains authoritative.
- No secrets belong in `VITE_*` variables.
