# Security policy

## Reporting a vulnerability

Please report security vulnerabilities privately through the repository's GitHub Security Advisories feature. Do not include working API keys, vault keys, passwords, private keys, or customer data in a public issue.

Include the affected Sentinel version, the deployment method, impact, and steps to reproduce with sanitized examples. The maintainers will acknowledge reports and coordinate a fix before public disclosure.

## Deployment notes

- Keep `.env` private and restrict it to the Sentinel operator.
- Keep `VAULT_KEY` backed up and unchanged; changing it makes stored connector credentials unreadable.
- Use HTTPS for access beyond a trusted local network.
- The current `API_KEY` is shared across dashboard clients. Do not treat it as per-user authentication or role-based authorization.
