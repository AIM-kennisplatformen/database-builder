import time
from pathlib import Path
from typing import Any

from loguru import logger

from database_builder_libs.models.abstract_sync_tracker import (
    AbstractSyncTracker,
    Artifact,
    ConflictItem,
)
from database_builder_libs.stores.sqlite.sqlite_store import SqliteRelationalStore

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

    Connect before first use::

        tracker = SqliteSyncTracker("my.db")
        tracker.connect()
        tracker.start_sync("Zotero")
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
        self._validate_identifier(self._table_sources, "table name")
        self._validate_identifier(self._table_artifacts, "table name")
        resolved = str(db_path) if db_path is not None else DEFAULT_DB_PATH
        SqliteRelationalStore.__init__(self, db_path=resolved, timeout=timeout)

    def _run_migrations(self, from_version: int) -> None:
        if from_version < 1:
            self._migrate_v1()

    def _migrate_v1(self) -> None:
        self.execute(
            f"CREATE TABLE IF NOT EXISTS {self._table_sources}(source_name TEXT PRIMARY KEY, last_sync_time REAL)"
        )
        self.execute(
            f"CREATE TABLE IF NOT EXISTS {self._table_artifacts}(item_key TEXT, source_name TEXT, modified_time REAL, last_sync_time REAL, PRIMARY KEY(item_key, source_name))"
        )
        self.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{self._table_artifacts}_item_key ON {self._table_artifacts}(item_key)"
        )

    def start_sync(self, source_name: str) -> float | None:
        """
        Return the last sync timestamp for a source, or register it as new.

        Parameters
        ----------
        source_name : str
            Unique identifier for the data source.

        Returns
        -------
        float | None
            Unix timestamp of the last successful sync, or None if the
            source has never been synchronized.
        """
        rows = self.query(self._table_sources, {"source_name": source_name})
        if rows:
            logger.info(
                "Source '{}' last synced at {}", source_name, rows[0]["last_sync_time"]
            )
            return rows[0]["last_sync_time"]
        self.insert(
            self._table_sources, {"source_name": source_name, "last_sync_time": None}
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
        Upsert artifact records and detect modification conflicts.

        Parameters
        ----------
        source_name : str
            Unique identifier for the data source.
        artifacts : list[Artifact]
            List of ``(item_key, modification_time)`` tuples from the source.

        Returns
        -------
        list[ConflictItem]
            Item keys where the same artifact has different modification
            times across sources.
        """
        now = time.time()
        for item_key, modified_time in artifacts:
            self.execute(
                f"INSERT INTO {self._table_artifacts} (item_key,source_name,modified_time,last_sync_time) VALUES(?,?,?,?) ON CONFLICT(item_key,source_name) DO UPDATE SET modified_time=excluded.modified_time, last_sync_time=excluded.last_sync_time",
                (item_key, source_name, modified_time.timestamp(), now),
            )
        self.update(
            self._table_sources, {"source_name": source_name}, {"last_sync_time": now}
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
        Remove artifact records older than a given timestamp.

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
        count = self.execute(
            f"DELETE FROM {self._table_artifacts} WHERE last_sync_time < ?",
            (before,),
        )
        self.commit()
        logger.info("Cleaned up {} old artifact record(s)", count)
        return count

    def sync_history(self, source_name: str) -> list[dict[str, Any]]:
        """
        Return all recorded artifacts for a given source.

        Parameters
        ----------
        source_name : str
            Unique identifier for the data source.

        Returns
        -------
        list[dict[str, Any]]
            Each dict contains ``item_key``, ``source_name``,
            ``modified_time``, and ``last_sync_time``.
        """
        return self.query_raw(
            f"SELECT item_key, source_name, modified_time, last_sync_time "
            f"FROM {self._table_artifacts} "
            "WHERE source_name=? "
            "ORDER BY last_sync_time DESC",
            (source_name,),
        )

    def sync_stats(self) -> dict[str, Any]:
        """
        Return aggregate statistics about the tracked sync state.

        Returns
        -------
        dict[str, Any]
            Keys: ``total_sources``, ``total_artifacts``,
            ``sources_with_conflicts``.
        """
        total_sources = self.query_raw(
            f"SELECT COUNT(*) AS count FROM {self._table_sources}"
        )[0]["count"]
        total_artifacts = self.query_raw(
            f"SELECT COUNT(*) AS count FROM {self._table_artifacts}"
        )[0]["count"]
        sources_with_conflicts = self.query_raw(
            f"SELECT COUNT(DISTINCT a.source_name) AS count "
            f"FROM {self._table_artifacts} a "
            f"JOIN {self._table_artifacts} b "
            f"ON a.item_key = b.item_key "
            f"AND a.source_name != b.source_name "
            f"AND a.modified_time != b.modified_time"
        )[0]["count"]
        return {
            "total_sources": total_sources,
            "total_artifacts": total_artifacts,
            "sources_with_conflicts": sources_with_conflicts,
        }

    def _find_conflicts(self, source_name: str) -> list[ConflictItem]:
        rows = self.query_raw(
            f"SELECT DISTINCT a.item_key "
            f"FROM {self._table_artifacts} a "
            f"JOIN {self._table_artifacts} b "
            f"ON a.item_key = b.item_key "
            f"WHERE a.source_name = ? "
            f"AND b.source_name != a.source_name "
            f"AND a.modified_time != b.modified_time",
            (source_name,),
        )
        return [row["item_key"] for row in rows]
