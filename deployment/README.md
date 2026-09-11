\# Agent 66 — Counselling Support Agent



\## 1. Overview



Agent 66 is a Counselling Support Agent designed to identify students who may benefit from professional counselling support and route them to appropriate human support.



The system is a recognition and routing system, not a counselling or therapy system.



The backend provides:



\- Counselling-support intake

\- Consent handling

\- Crisis detection

\- Urgency triage

\- Referral management

\- Counsellor assignment

\- Referral status tracking

\- Immediate crisis escalation

\- Appointment scheduling

\- Restricted counselling records

\- Follow-up tracking

\- Academic accommodation coordination

\- Wellbeing resource directory

\- Anonymous aggregate reporting

\- Authentication and role-based access control

\- Encrypted persistent database

\- Audit logging



\---



\## 2. Technology Stack



\- Python

\- FastAPI

\- Uvicorn

\- Pydantic

\- Pydantic Settings

\- SQLCipher

\- SQLite-compatible database interface

\- Google Generative AI integration support

\- Custom authentication and RBAC



\---



\## 3. Project Structure



```text

counselling-support-agent/

│

├── backend/

│   ├── app/

│   │   ├── agents/

│   │   │   └── counselling\_agent/

│   │   ├── api/

│   │   ├── auth/

│   │   ├── core/

│   │   ├── database/

│   │   ├── models/

│   │   ├── safety/

│   │   └── services/

│   │

│   ├── counselling\_agent\_encrypted.db

│   ├── requirements.txt

│   └── start\_production.bat

│

├── frontend/

├── tests/

├── data/

├── deployment/

├── .env

├── .env.example

└── README.md

