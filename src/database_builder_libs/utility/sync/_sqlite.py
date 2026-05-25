import time
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from database_builder_libs.stores.sqlite._relational import SqliteRelationalStore
from database_builder_libs.utility.sync._base import (
    AbstractSyncTracker,
    Artifact,
    ConflictItem,
)

DEFAULT_DB_PATH = "partial_sync.db"


class SqliteSyncTracker(SqliteRelationalStore, AbstractSyncTracker):
    """
    SQLite-backed sync tracker that delegates storage to SqliteRelationalStore.

    Parameters
    ----------
    db_path : str | Path | None
        Path to the SQLite database file. Use ``:memory:`` for an
        in-memory database. Defaults to ``"partial_sync.db"``.
    table_sources : str
        Name of the sources table. Default ``"sources"``.
    table_artifacts : str
        Name of the artifacts table. Default ``"artifacts"``.
    timeout : float
        Connection timeout in seconds. Default ``5.0``.
    """

    SCHEMA_VERSION: int = 1

    def __init__(
        self,
        db_path: str | Path | None = None,
        *,
        table_sources: str = "sources",
        table_artifacts: str = "artifacts",
        timeout: float = 5.0,
    ) -> None:
        self._table_sources = table_sources
        self._table_artifacts = table_artifacts
        resolved = str(db_path) if db_path is not None else DEFAULT_DB_PATH
        SqliteRelationalStore.__init__(self, db_path=resolved, timeout=timeout)

    def _run_migrations(self, from_version: int) -> None:
        if from_version < 1:
            self._migrate_v1()

    def _migrate_v1(self) -> None:
        cur = self.cursor()
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table_sources}(
                source_name TEXT PRIMARY KEY,
                last_sync_time REAL
            )
            """
        )
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table_artifacts}(
                item_key TEXT,
                source_name TEXT,
                modified_time REAL,
                last_sync_time REAL,
                PRIMARY KEY(item_key, source_name)
            )
            """
        )
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self._table_artifacts}_item_key
            ON {self._table_artifacts}(item_key)
            """
        )

    def start_sync(self, source_name: str) -> Optional[float]:
        """Return the last sync timestamp for the source."""
        cur = self.execute(
            f"SELECT last_sync_time FROM {self._table_sources} "
            "WHERE source_name=?",
            (source_name,),
        )
        row = cur.fetchone()
        if row:
            logger.info("Source '{}' last synced at {}", source_name, row[0])
            return row[0]
        self.execute(
            f"INSERT INTO {self._table_sources}(source_name,last_sync_time) "
            "VALUES (?,NULL)",
            (source_name,),
        )
        self.commit()
        logger.info("Registered new source '{}'", source_name)
        return None

    def finish_sync(
        self,
        source_name: str,
        artifacts: list[Artifact],
    ) -> list[ConflictItem]:
        """
        Insert artifacts reported by the source and return
        artifacts requiring reconciliation.
        """
        now = time.time()
        rows = [
            (item_key, source_name, modified_time.timestamp(), now)
            for item_key, modified_time in artifacts
        ]
        self.executemany(
            f"""
            INSERT INTO {self._table_artifacts}
                (item_key,source_name,modified_time,last_sync_time)
            VALUES(?,?,?,?)
            ON CONFLICT(item_key,source_name)
            DO UPDATE SET
                modified_time=excluded.modified_time,
                last_sync_time=excluded.last_sync_time
            """,
            rows,
        )
        self.execute(
            f"UPDATE {self._table_sources} "
            "SET last_sync_time=? WHERE source_name=?",
            (now, source_name),
        )
        self.commit()
        conflicts = self._find_conflicts(source_name)
        if conflicts:
            logger.warning(
                "Found {} conflicting artifact(s) for source '{}': {}",
                len(conflicts),
                source_name,
                conflicts,
            )
        else:
            logger.info(
                "Finished sync for source '{}' ({} artifacts, no conflicts)",
                source_name,
                len(artifacts),
            )
        return conflicts

    def cleanup_old_records(self, before: float) -> int:
        """
        Remove artifact records older than the given timestamp.

        Parameters
        ----------
        before : float
            Unix timestamp. Records with ``last_sync_time < before``
            are deleted.

        Returns
        -------
        int
            Number of deleted artifact rows.
        """
        cur = self.execute(
            f"DELETE FROM {self._table_artifacts} WHERE last_sync_time < ?",
            (before,),
        )
        self.commit()
        logger.info("Cleaned up {} old artifact record(s)", cur.rowcount)
        return cur.rowcount

    def sync_history(self, source_name: str) -> list[dict[str, Any]]:
        """
        Return sync history for a given source.

        Parameters
        ----------
        source_name : str
            Unique identifier for the data source.

        Returns
        -------
        list[dict[str, Any]]
            Each dict contains the keys ``item_key``, ``source_name``,
            ``modified_time``, and ``last_sync_time``.
        """
        cur = self.execute(
            f"SELECT item_key, source_name, modified_time, last_sync_time "
            f"FROM {self._table_artifacts} "
            "WHERE source_name=? "
            "ORDER BY last_sync_time DESC",
            (source_name,),
        )
        return [
            {
                "item_key": row[0],
                "source_name": row[1],
                "modified_time": row[2],
                "last_sync_time": row[3],
            }
            for row in cur.fetchall()
        ]

    def sync_stats(self) -> dict[str, Any]:
        """
        Return aggregate statistics about the tracked sync state.

        Returns
        -------
        dict[str, Any]
            Keys: ``total_sources``, ``total_artifacts``,
            ``sources_with_conflicts``.
        """
        total_sources = self.execute(
            f"SELECT COUNT(*) FROM {self._table_sources}"
        ).fetchone()[0]
        total_artifacts = self.execute(
            f"SELECT COUNT(*) FROM {self._table_artifacts}"
        ).fetchone()[0]
        sources_with_conflicts = self.execute(
            f"""
            SELECT COUNT(DISTINCT a.source_name)
            FROM {self._table_artifacts} a
            JOIN {self._table_artifacts} b
              ON a.item_key = b.item_key
             AND a.source_name != b.source_name
             AND a.modified_time != b.modified_time
            """
        ).fetchone()[0]
        return {
            "total_sources": total_sources,
            "total_artifacts": total_artifacts,
            "sources_with_conflicts": sources_with_conflicts,
        }

    def _find_conflicts(self, source_name: str) -> list[ConflictItem]:
        """Return item_keys where sources disagree on modification time."""
        cur = self.execute(
            f"""
            SELECT DISTINCT a.item_key
            FROM {self._table_artifacts} a
            JOIN {self._table_artifacts} b
              ON a.item_key = b.item_key
            WHERE a.source_name = ?
              AND b.source_name != a.source_name
              AND a.modified_time != b.modified_time
            """,
            (source_name,),
        )
        return [row[0] for row in cur.fetchall()]
