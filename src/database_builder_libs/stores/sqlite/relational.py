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
    """Retry a database operation on sqlite3.OperationalError."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self: "SqliteRelationalStore", *args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(self, *args, **kwargs)
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
            logger.error("Database operation failed after {} attempts", max_attempts)
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
    """

    SCHEMA_VERSION: int = 0

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        timeout: float = 5.0,
    ) -> None:
        self._db_path = str(db_path)
        self._timeout = timeout

        self.conn = sqlite3.connect(self._db_path, timeout=self._timeout)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

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
            """
            CREATE TABLE IF NOT EXISTS _schema_version(
                version INTEGER PRIMARY KEY
            )
            """
        )

    def _get_schema_version(self) -> int:
        cur = self.conn.execute("SELECT MAX(version) FROM _schema_version")
        row = cur.fetchone()
        return row[0] if row and row[0] is not None else 0

    def _set_schema_version(self, version: int) -> None:
        self.conn.execute(
            "INSERT INTO _schema_version(version) VALUES (?)", (version,)
        )

    def _run_migrations(self, from_version: int) -> None:
        """Override in subclasses to define schema migrations."""

    @_retry()
    def execute(self, sql: str, params: tuple | list | None = None) -> Any:
        return self.conn.execute(sql, params or ())

    @_retry()
    def executemany(self, sql: str, rows: list[tuple]) -> None:
        self.conn.executemany(sql, rows)

    @_retry()
    def commit(self) -> None:
        self.conn.commit()

    def cursor(self) -> Any:
        return self.conn.cursor()

    def close(self) -> None:
        self.conn.close()
        logger.debug("Database connection closed")
