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

Create the first administrator account from the dashboard on first visit. Additional accounts and roles are managed in Settings �w^~)�v Accounts and access. Browser sessions expire after 12 hours; password changes and account changes use CSRF protection. The API health endpoint is public for container health checks.

The dashboard stores the key in that browser's local settings. Use HTTPS when exposing Sentinel beyond a trusted local network.


## Inbound message translation

Webhook, MQTT, REST API polling, and WebSocket messages are translated into Sentinel's common event fields before storage and rule evaluation. Automatic detection recognizes common names such as `event_type`, `message`, `level`, `data`, and `device.name`. A connector can override any field with a dot-separated JSON object path under its translation settings. REST polling accepts JSON responses and suppresses repeat observations for unchanged event objects. WebSocket streams reconnect automatically after connection loss.

Example field map:

    {
      "summary": "alarm.message",
      "severity": "alarm.priority",
      "entity": "device.name",
      "value": "sensor.reading"
    }

Supported targets are `type`, `severity`, `summary`, `timestamp`, `entity`, `entity_id`, and `value`. Original source JSON is retained in each observation's raw data. This first translation layer normalizes incoming data into Sentinel; sending translated data to another system and routing messages between connectors are later capabilities.
