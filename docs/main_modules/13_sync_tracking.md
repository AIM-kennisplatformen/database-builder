# Sync tracking

The sync tracking module provides an abstract interface (`AbstractSyncTracker` in `database_builder_libs.models.abstract_sync_tracker`) and a SQLite-backed implementation (`SqliteSyncTracker` in `database_builder_libs.utility.sync._sqlite`) for tracking per-source synchronization state and detecting artifact modification conflicts.

`SqliteSyncTracker` inherits from `SqliteRelationalStore` (`database_builder_libs.stores.sqlite.sqlite_store`), which implements `AbstractRelationalStore` (`database_builder_libs.models.abstract_relational_store`) — a generic CRUD wrapper around SQLite with retry, WAL mode, and schema migration support.

## Pattern

The typical sync workflow has three steps:

1. **`start_sync(source_name)`** — retrieve the last known sync timestamp for a source (or `None` if first sync)
2. **Fetch artifacts** — pass the timestamp to the source (e.g., `ZoteroSource.get_list_artefacts`) to get only changed items
3. **`finish_sync(source_name, artifacts)`** — upsert artifact records, update the source timestamp, and return any conflicting item keys

```python
from database_builder_libs.utility.sync._sqlite import SqliteSyncTracker

tracker = SqliteSyncTracker()
tracker.connect()

last_sync = tracker.start_sync("Zotero")
last_sync_dt = (
    datetime.fromtimestamp(last_sync) if last_sync is not None else None
)

artifacts = zot.get_list_artefacts(last_synced=last_sync_dt)
conflicts = tracker.finish_sync("Zotero", artifacts)

if conflicts:
    print(f"Conflicts detected: {conflicts}")

tracker.close()
```

## Database schema

The SQLite implementation uses two configurable tables:

### `sources` table (default name)

| Column | Type | Description |
|---|---|---|
| `source_name` | TEXT PRIMARY KEY | Unique source identifier |
| `last_sync_time` | REAL | Unix timestamp of last successful sync |

### `artifacts` table (default name)

| Column | Type | Description |
|---|---|---|
| `item_key` | TEXT | Artifact identifier |
| `source_name` | TEXT | Source that reported this artifact |
| `modified_time` | REAL | Artifact's modification time in the source |
| `last_sync_time` | REAL | When this artifact was last synchronized |

Primary key is `(item_key, source_name)`. An index on `item_key` supports conflict detection joins.

### `_schema_version` table

Internal table tracking the database schema version for migrations.

## SqliteSyncTracker

### Configuration

```python
SqliteSyncTracker(
    db_path="partial_sync.db",  # Path or ":memory:"
    table_sources="sources",     # Custom sources table name
    table_artifacts="artifacts", # Custom artifacts table name
    timeout=5.0,                 # SQLite connection timeout
)
```

### Methods

| Method | Returns | Description |
|---|---|---|
| `start_sync(source_name)` | `float \| None` | Last sync timestamp or None for new sources |
| `finish_sync(source_name, artifacts)` | `list[str]` | Upserts artifacts, returns conflicting item keys |
| `cleanup_old_records(before)` | `int` | Deletes artifact records older than timestamp |
| `sync_history(source_name)` | `list[dict]` | All recorded artifacts for a source |
| `sync_stats()` | `dict` | Aggregate counts (sources, artifacts, conflicts) |
| `close()` | — | Closes the database connection |

### Conflict detection

A conflict occurs when two sources report the same artifact (`item_key`) with different `modified_time` values. This typically indicates the artifact was updated in one source but not in another.

The `finish_sync` method automatically checks for conflicts and returns the problematic item keys. After reconciliation (updating the conflicting source), the conflict is resolved.

### SqliteRelationalStore layer

`SqliteRelationalStore` provides the low-level CRUD interface inherited by `SqliteSyncTracker`. Use it directly when you need a simple SQLite-backed store without sync logic:

```python
from database_builder_libs.stores.sqlite.sqlite_store import SqliteRelationalStore

store = SqliteRelationalStore("my.db")
store.insert("users", {"id": 1, "name": "Alice"})
rows = store.query("users", {"name": "Alice"})
store.update("users", {"id": 1}, {"name": "Bob"})
store.delete("users", {"id": 1})
store.close()
```

| Method | Returns | Description |
|---|---|---|
| `insert(table, row)` | `None` | Insert a single row (dict) |
| `query(table, filter)` | `list[dict]` | Query with equality filter; `None`/`{}` returns all |
| `update(table, filter, values)` | `int` | Update matching rows, returns count |
| `delete(table, filter)` | `int` | Delete matching rows, returns count |
| `query_raw(sql, params)` | `list[dict]` | Raw SELECT with `?` placeholders |
| `execute(sql, params)` | `int` | Raw DML/DDL, returns affected rows |
| `commit()` | `None` | Explicit commit |

Implement `AbstractRelationalStore` to back the same CRUD API with other databases (PostgreSQL, DuckDB, etc.).

## Error handling

Database operations are wrapped with automatic retry (3 attempts with exponential backoff) for `sqlite3.OperationalError` (e.g., database lock). All operations are logged via `loguru`.

## In-memory database

Use `:memory:` as the database path for testing:

```python
tracker = SqliteSyncTracker(db_path=":memory:")
```

## Custom database backends

There are two levels you can implement:

1. **Implement `AbstractRelationalStore`** for a new database backend, then reuse `SqliteSyncTracker`'s logic (it calls only CRUD methods + `query_raw`/`execute`):
   ```python
   from database_builder_libs.models.abstract_relational_store import AbstractRelationalStore

   class PostgresRelationalStore(AbstractRelationalStore):
       def insert(self, table, row): ...
       def query(self, table, filter): ...
       # ...
   ```

2. **Implement `AbstractSyncTracker` directly** for a completely different storage model:
   ```python
   from database_builder_libs.models.abstract_sync_tracker import AbstractSyncTracker, Artifact, ConflictItem

   class CustomSyncTracker(AbstractSyncTracker):
       def start_sync(self, source_name: str) -> float | None: ...
       def finish_sync(self, source_name: str, artifacts: list[Artifact]) -> list[ConflictItem]: ...
       def close(self) -> None: ...
   ```

## Troubleshooting

| Problem | Likely cause | Solution |
|---|---|---|
| `sqlite3.OperationalError: database is locked` | Concurrent access | Increase `timeout` or reduce concurrent writers |
| `sqlite3.OperationalError: no such table` | Schema version mismatch | Delete the `.db` file and let it recreate |
| Unexpected conflicts | Sources reporting different timestamps | Verify source clocks are synchronized (UTC) |
