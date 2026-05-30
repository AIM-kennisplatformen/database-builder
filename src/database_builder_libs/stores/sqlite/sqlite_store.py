import sqlite3
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from loguru import logger

from database_builder_libs.models.abstract_relational_store import (
    AbstractRelationalStore,
)


def _retry(max_attempts: int = 3, base_delay: float = 0.1) -> Callable:
    """
    Retry a database operation on :class:`sqlite3.OperationalError`.

    Only ``OperationalError`` is retried — it covers transient conditions
    such as a locked database or I/O interruption.  Other
    ``sqlite3`` exceptions (``ProgrammingError``, ``IntegrityError``,
    ``DataError``, ``NotSupportedError``) indicate programming bugs or
    data-integrity violations and are allowed to propagate immediately.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: "SqliteRelationalStore", *args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except sqlite3.OperationalError as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "Database operation failed (attempt {}/{}): {}."
                            " Retrying in {:.1f}s...",
                            attempt,
                            max_attempts,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
            logger.error(
                "Database operation failed after {} attempts", max_attempts
            )
            raise RuntimeError(
                f"Database operation failed after {max_attempts} attempts"
            ) from last_exc

        return wrapper

    return decorator


class SqliteRelationalStore(AbstractRelationalStore):
    """
    SQLite-backed implementation of AbstractRelationalStore.

    Provides automatic retry with exponential backoff on
    ``sqlite3.OperationalError``, schema migration infrastructure
    via ``SCHEMA_VERSION`` / ``_run_migrations()``, and WAL mode.

    Subclasses can set ``SCHEMA_VERSION`` and override
    ``_run_migrations()`` to define their own schema.

    Usage::

        store = SqliteRelationalStore("my.db")
        store.connect()
        store.insert("users", {"id": 1, "name": "Alice"})
        store.close()
    """

    SCHEMA_VERSION: int = 0

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        timeout: float = 5.0,
    ) -> None:
        super().__init__()
        self._db_path = str(db_path)
        self._timeout = timeout

    def _connect_impl(self, config: dict | None = None) -> None:
        self.conn = sqlite3.connect(self._db_path, timeout=self._timeout)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

    def _validate_identifier(self, name: str, context: str = "identifier") -> None:
        if not name.isidentifier():
            raise ValueError(
                f"Invalid {context}: {name!r}. Must be a valid SQL identifier"
            )

    def _init_db(self) -> None:
        """Create or migrate the database schema to match SCHEMA_VERSION."""
        self._create_schema_version_table()
        current_version = self._get_schema_version()
        if current_version < self.SCHEMA_VERSION:
            logger.info(
                "Migrating database from schema v{} to v{}",
                current_version,
                self.SCHEMA_VERSION,
            )
            self._run_migrations(current_version)
            self._set_schema_version(self.SCHEMA_VERSION)
            self.conn.commit()

    def _create_schema_version_table(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS _schema_version("
            "version INTEGER PRIMARY KEY)"
        )

    def _get_schema_version(self) -> int:
        cursor = self.conn.execute("SELECT MAX(version) FROM _schema_version")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    def _set_schema_version(self, version: int) -> None:
        self.conn.execute(
            "INSERT INTO _schema_version(version) VALUES (?)", (version,)
        )

    def _run_migrations(self, from_version: int) -> None:
        """Override in subclasses to define schema migrations."""

    @_retry()
    def insert(self, table: str, row: dict[str, Any]) -> None:
        self._ensure_connected()
        self._validate_identifier(table, "table name")
        for column in row:
            self._validate_identifier(column, "column name")
        columns = ", ".join(row)
        placeholders = ", ".join("?" for _ in row)
        self.conn.execute(
            f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
            tuple(row.values()),
        )

    @_retry()
    def query(
        self,
        table: str,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_connected()
        self._validate_identifier(table, "table name")
        if filter:
            for column in filter:
                self._validate_identifier(column, "column name")
            where = " AND ".join(f"{k}=?" for k in filter)
            cursor = self.conn.execute(
                f"SELECT * FROM {table} WHERE {where}",
                tuple(filter.values()),
            )
        else:
            cursor = self.conn.execute(f"SELECT * FROM {table}")
        return self._rows_to_dicts(cursor)

    @_retry()
    def update(
        self,
        table: str,
        filter: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        self._ensure_connected()
        self._validate_identifier(table, "table name")
        for column in values:
            self._validate_identifier(column, "column name")
        for column in filter:
            self._validate_identifier(column, "column name")
        set_clause = ", ".join(f"{k}=?" for k in values)
        where = " AND ".join(f"{k}=?" for k in filter)
        cursor = self.conn.execute(
            f"UPDATE {table} SET {set_clause} WHERE {where}",
            tuple(values.values()) + tuple(filter.values()),
        )
        return cursor.rowcount

    @_retry()
    def delete(self, table: str, filter: dict[str, Any]) -> int:
        self._ensure_connected()
        self._validate_identifier(table, "table name")
        for column in filter:
            self._validate_identifier(column, "column name")
        where = " AND ".join(f"{k}=?" for k in filter)
        cursor = self.conn.execute(
            f"DELETE FROM {table} WHERE {where}",
            tuple(filter.values()),
        )
        return cursor.rowcount

    @_retry()
    def query_raw(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_connected()
        cursor = self.conn.execute(sql, params or ())
        return self._rows_to_dicts(cursor)

    @_retry()
    def execute(self, sql: str, params: tuple | list | None = None) -> int:
        self._ensure_connected()
        cursor = self.conn.execute(sql, params or ())
        return cursor.rowcount

    @_retry()
    def commit(self) -> None:
        self._ensure_connected()
        self.conn.commit()

    def close(self) -> None:
        if not self._connected:
            return
        self.conn.close()
        self._connected = False
        logger.debug("Database connection closed")

    @staticmethod
    def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
