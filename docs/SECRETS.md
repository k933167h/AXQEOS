# Secrets management
1. GitHub repository Settings -> Secrets and variables -> Actions -> New repository secret.
2. Configure AX_REPORTER_TOKEN, AX_SME_TOKEN, JEV_API_KEY, LLM_JUDGE_API_KEY, PLANE_API_KEY, KIWI_API_TOKEN, LANGFUSE_INGEST_TOKEN as secrets.
3. Configure JEV_BASE_URL, JEV_MODEL, LLM_JUDGE_BASE_URL, LLM_JUDGE_MODEL, PLANE_ISSUE_URL, KIWI_RESULT_URL, LANGFUSE_INGEST_URL as variables where appropriate.
4. Protect the integration environment with required reviewers and restricted deployment branches.
5. Production: use a Secret Manager with GitHub OIDC and least-privilege, short-lived credentials. Do not use secrets in forked PR tests.
6. Keep .env ignored. Rotate leaked credentials immediately. Public repository: never commit confidential evidence.
7. Current workflow only validates that integration secrets exist; it does not execute the full external E2E flow.
