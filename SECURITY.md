# Security policy

## Reporting a vulnerability

Please report security vulnerabilities privately through the repository's GitHub Security Advisories feature. Do not include vault keys, passwords, private keys, or customer data in a public issue.

Include the affected Sentinel version, the deployment method, impact, and steps to reproduce with sanitized examples. The maintainers will acknowledge reports and coordinate a fix before public disclosure.

## Deployment notes

- Keep `.env` private and restrict it to the Sentinel operator.
- Keep `VAULT_KEY` backed up and unchanged; changing it makes stored connector credentials unreadable.
- Use HTTPS for access beyond a trusted local network.
- Sentinel accounts have administrator, operator, and viewer roles. Protect administrator credentials and use HTTPS for remote access.
- Browser sessions expire after 12 hours; disabling an account invalidates its sessions.
