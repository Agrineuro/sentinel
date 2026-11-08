from sqlalchemy import Engine, inspect

def apply_migrations(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Sentinel's current migration runner supports SQLite only")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        applied = set(connection.exec_driver_sql("SELECT version FROM schema_migrations").scalars().all())
        if 1 not in applied:
            columns = {column["name"] for column in inspect(connection).get_columns("rules")}
            for name, sql_type in {
                "condition_field": "VARCHAR(160)",
                "condition_operator": "VARCHAR(8)",
                "condition_value": "FLOAT",
            }.items():
                if name not in columns:
                    connection.exec_driver_sql("ALTER TABLE rules ADD COLUMN " + name + " " + sql_type)
            connection.exec_driver_sql("INSERT OR IGNORE INTO schema_migrations (version) VALUES (1)")
        if 2 not in applied:
            connection.exec_driver_sql(
                "CREATE TABLE IF NOT EXISTS connectors ("
                "id VARCHAR NOT NULL PRIMARY KEY, name VARCHAR NOT NULL, connector_type VARCHAR NOT NULL, "
                "direction VARCHAR NOT NULL DEFAULT 'inbound', enabled BOOLEAN NOT NULL DEFAULT 0, "
                "status VARCHAR NOT NULL DEFAULT 'disabled', config JSON NOT NULL DEFAULT '{}', "
                "credential_id VARCHAR, webhook_token_hash VARCHAR, last_checked_at DATETIME, "
                "last_error TEXT, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            )
            connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_connectors_id ON connectors (id)")
            connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_connectors_name ON connectors (name)")
            connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_connectors_connector_type ON connectors (connector_type)")
            connection.exec_driver_sql("INSERT OR IGNORE INTO schema_migrations (version) VALUES (2)")
