#!/usr/bin/env python3
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings


def database_path() -> Path:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        raise SystemExit("This backup command currently supports SQLite databases only.")
    raw = url[len("sqlite:///"):]
    return Path(raw).resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a consistent SQLite backup of Sentinel.")
    parser.add_argument("destination", nargs="?", help="Backup file path (defaults to ./backups with a UTC timestamp)")
    args = parser.parse_args()
    source = database_path()
    if not source.is_file():
        raise SystemExit("Database file does not exist: " + str(source))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = Path(args.destination).expanduser() if args.destination else Path("backups") / ("sentinel-" + stamp + ".sqlite3")
    destination = destination.resolve()
    parent_existed = destination.parent.exists()
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not parent_existed:
        os.chmod(destination.parent, 0o700)
    source_db = sqlite3.connect(str(source), timeout=30)
    try:
        target_db = sqlite3.connect(str(destination))
        try:
            source_db.backup(target_db)
            check = target_db.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise RuntimeError("Backup integrity check failed: " + str(check))
            target_db.commit()
        finally:
            target_db.close()
    finally:
        source_db.close()
    os.chmod(destination, 0o600)
    print(str(destination))


if __name__ == "__main__":
    main()
