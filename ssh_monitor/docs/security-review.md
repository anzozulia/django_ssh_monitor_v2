# Security Review Notes

Date: 2026-02-26

## Scope

- Authentication requirements on application views
- SSH credential encryption at rest
- Production build-time configuration guardrails

## Findings

- Most application views use `LoginRequiredMixin` and require authenticated sessions.
- Sensitive SSH credentials are encrypted using Fernet (`CREDENTIAL_ENCRYPTION_KEY`) before persistence.
- Production settings fail fast when `DATABASE_URL` is missing.
- Notification channel secrets are stored encrypted in `NotificationChannel.config_encrypted`.

## Follow-ups

- Coverage for service-layer security edge cases remains below the target threshold and should be increased in a dedicated hardening pass.
- Consider adding stricter CSRF/security header assertions in integration tests for critical endpoints.
