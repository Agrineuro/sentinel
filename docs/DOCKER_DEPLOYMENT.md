# Docker deployment

## Requirements

- A Linux host with Docker Engine and Docker Compose v2.
- At least 2 GB of available memory for a small installation.
- Network access from Sentinel Core to every system it monitors or polls.

## First install

From the repository root, run:

    ./scripts/install-docker.sh

The script creates a private `.env` with a random vault encryption key, then builds and starts the containers. It does not install Docker on the host.

Open the URL shown by the installer and create the first administrator account. Administrators can add accounts later in **Settings"��y��y� Accounts and access**. Keep `.env` private. Back up `VAULT_KEY` securely and keep it unchanged; Sentinel needs the original key to decrypt stored connector credentials.

By default, the web port is bound to `127.0.0.1`. Core is available only on the internal Compose network and is reverse-proxied by the dashboard container.

## Allow access from your LAN

Set `SENTINEL_BIND=0.0.0.0` in `.env`, then run:

    docker compose up -d

Restrict access with your firewall. For access beyond a trusted local network, place Sentinel behind a TLS reverse proxy and use HTTPS. Sentinel uses individual administrator, operator, and viewer accounts. HTTPS protects passwords and session cookies in transit.

## Everyday operations

Show status:

    docker compose ps

Follow logs:

    docker compose logs -f --tail=100

Apply repository updates:

    git pull
    docker compose up -d --build

Stop Sentinel while keeping its data:

    docker compose down

Do not use `docker compose down -v` unless you intend to delete Sentinel's database volume.

## Back up and restore

Create a consistent SQLite backup in the container:

    docker compose exec -T core python scripts/backup_database.py /data/sentinel-backup.sqlite3

Copy it to the host:

    docker compose cp core:/data/sentinel-backup.sqlite3 ./sentinel-backup.sqlite3

Keep a copy off the Sentinel host. The backup contains infrastructure inventory and observations.

To restore, first make a backup of the current database, then stop Core and copy the restore file into its data volume:

    docker compose exec -T core python scripts/backup_database.py /data/before-restore.sqlite3
    docker compose cp core:/data/before-restore.sqlite3 ./before-restore.sqlite3
    docker compose stop core
    docker compose cp ./sentinel-backup.sqlite3 core:/data/restore.sqlite3
    docker compose exec -T core sh -c 'cp /data/restore.sqlite3 /data/sentinel.db && chown 10001:10001 /data/sentinel.db'
    docker compose start core

The copied database must be owned by UID 10001 inside the container so Core can open it.

## Configuration

The installer creates `.env`. `.env.example` documents the available settings. Account passwords are stored as bcrypt hashes. Browser sessions expire after 12 hours and use CSRF protection for changes. Keep `VAULT_KEY` stable for the lifetime of the credential store. An `API_KEY` entry left by an older installation is ignored by account authentication.

The SQLite database lives in the `sentinel_data` named volume at `/data/sentinel.db`. This deployment target currently supports SQLite. Core health checks verify the API and database before the dashboard container starts.
