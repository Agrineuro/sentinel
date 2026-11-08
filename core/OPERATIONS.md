# Sentinel Core Operations

## Database location

Sentinel uses SQLite by default at core/sentinel.db. Set DATABASE_URL in core/.env to select a different SQLite file. The current migration runner is SQLite-only and fails startup for other database dialects so an unsupported database cannot silently skip schema changes.

## Back up

From the core directory, run:

    .venv/bin/python scripts/backup_database.py

The command creates a transaction-consistent SQLite backup under core/backups/, runs an integrity check, and restricts the backup file to the service account. A custom destination can be passed as the first argument.

Store backups outside the machine hosting Sentinel if they need to survive disk loss. Keep the backup directory private because observations and inventory may contain sensitive infrastructure details.

## Restore

1. Stop the Sentinel API process.
2. Preserve the current database file as a separate recovery copy.
3. Copy the chosen backup to the configured database path.
4. Start the API and check /api/v1/health; it reports database status.
5. Confirm expected systems, observations, rules, and alerts are visible.

The startup migration runner records applied schema versions and applies SQLite changes idempotently before serving requests.


## API access control

Set API_KEY to a long random value in core/.env. Set ENVIRONMENT=production to require an API key; production mode refuses API requests if no key is configured. Enter the same key in Settings → Backend connection → API key in each browser. The key stays out of the frontend build and is sent in an authorization header for REST and a WebSocket subprotocol for live events. The health endpoint remains public and reports whether authentication is required.

The dashboard stores the key in that browser's local settings. Use HTTPS when exposing Sentinel beyond a trusted local network.
