\# Agent 66 — Deployment Checklist



\## Configuration



\- \[ ] ENVIRONMENT is set to production

\- \[ ] Production AUTH\_SECRET\_KEY configured

\- \[ ] Production DATABASE\_ENCRYPTION\_KEY configured

\- \[ ] TOKEN\_EXPIRY\_SECONDS verified

\- \[ ] Production secrets are not committed to source control



\## Database



\- \[ ] SQLCipher database exists

\- \[ ] Database opens with the configured encryption key

\- \[ ] Database is not plaintext SQLite

\- \[ ] No plaintext database backup is included in the deployment package

\- \[ ] Database backup and retention policy defined



\## Application



\- \[ ] Dependencies installed

\- \[ ] Python compilation passes

\- \[ ] Application startup passes

\- \[ ] Root endpoint passes

\- \[ ] Health endpoint passes

\- \[ ] Swagger documentation passes

\- \[ ] OpenAPI specification passes



\## Authentication



\- \[ ] Valid credentials authenticate successfully

\- \[ ] Invalid passwords are rejected

\- \[ ] Token expiry is configured

\- \[ ] Password hashes are not returned by API responses



\## RBAC



\- \[ ] Student permissions verified

\- \[ ] Counsellor permissions verified

\- \[ ] Mentor permissions verified

\- \[ ] Faculty permissions verified

\- \[ ] HOD permissions verified

\- \[ ] Dean permissions verified

\- \[ ] Admin permissions verified



\## Safety



\- \[ ] Consent enforcement verified

\- \[ ] Crisis detection verified

\- \[ ] Immediate crisis escalation verified

\- \[ ] Approved crisis resources verified

\- \[ ] Counselling is not presented as diagnosis or therapy



\## Sensitive Data



\- \[ ] Counselling records are restricted

\- \[ ] Unauthorized roles cannot access restricted records

\- \[ ] Aggregate reporting preserves privacy thresholds

\- \[ ] Audit logging is enabled



\## Infrastructure



\- \[ ] HTTPS configured

\- \[ ] Firewall/network rules reviewed

\- \[ ] Production secret management configured

\- \[ ] Monitoring configured

\- \[ ] Backup strategy configured

\- \[ ] Recovery procedure documented

\- \[ ] Log retention configured



\## Governance



\- \[ ] Institutional approval obtained

\- \[ ] Named human escalation contacts verified

\- \[ ] Emergency contacts verified

\- \[ ] Data retention policy verified

\- \[ ] Access roles reviewed

\- \[ ] Final safety review completed



\## Regression Testing



Phase 19 final regression:



\- Total tests: 75

\- Passed: 75

\- Failed: 0



Status:



\*\*READY FOR FINAL REVIEW\*\*

