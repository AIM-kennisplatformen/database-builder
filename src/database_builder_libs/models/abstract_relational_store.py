from abc import ABC, abstractmethod
from typing import Any


class AbstractRelationalStore(ABC):
    """
    Abstract domain-level interface for a relational data store.

    Provides CRUD operations (``insert``, ``query``, ``update``,
    ``delete``) with dictionary-based row representations, plus
    ``query_raw`` / ``execute`` escape hatches for complex SQL.

    Implementations can use SQLite, PostgreSQL, or any other
    relational backend.
    """

    def __init__(self) -> None:
        self._connected: bool = False
        self._connecting: bool = False

    def connect(self, config: dict | None = None) -> None:
        """
        Establish connection to the backend.

        This method is idempotent. Calling it multiple times is safe.

        Parameters
        ----------
        config : dict | None
            Backend-specific configuration.

        Raises
        ------
        ConnectionError
            Backend unreachable.
        RuntimeError
            Backend misconfigured.
        """
        if self._connected:
            return
        self._connecting = True
        try:
            self._connect_impl(config)
            self._connected = True
        finally:
            self._connecting = False

    @abstractmethod
    def _connect_impl(self, config: dict | None = None) -> None:
        """Backend-specific connection logic."""

    def _ensure_connected(self) -> None:
        if not (self._connected or self._connecting):
            raise RuntimeError(
                f"{self.__class__.__name__} used before connect() was called"
            )

    @abstractmethod
    def insert(self, table: str, row: dict[str, Any]) -> None:
        """
        Insert a single row into a table.

        Parameters
        ----------
        table : str
            Target table name.
        row : dict[str, Any]
            Column-value mapping for the new row.
        """
        ...

    @abstractmethod
    def query(
        self,
        table: str,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query rows from a table with equality-based filters.

        Parameters
        ----------
        table : str
            Target table name.
        filter : dict[str, Any] | None
            Column-value pairs for WHERE equality clauses.
            ``None`` or empty dict returns all rows.

        Returns
        -------
        list[dict[str, Any]]
            Matching rows as column-value mappings.
        """
        ...

    @abstractmethod
    def update(
        self,
        table: str,
        filter: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        """
        Update rows matching an equality-based filter.

        Parameters
        ----------
        table : str
            Target table name.
        filter : dict[str, Any]
            Column-value pairs for WHERE equality clauses.
        values : dict[str, Any]
            Column-value pairs to set.

        Returns
        -------
        int
            Number of rows updated.
        """
        ...

    @abstractmethod
    def delete(
        self,
        table: str,
        filter: dict[str, Any],
    ) -> int:
        """
        Delete rows matching an equality-based filter.

        Parameters
        ----------
        table : str
            Target table name.
        filter : dict[str, Any]
            Column-value pairs for WHERE equality clauses.

        Returns
        -------
        int
            Number of rows deleted.
        """
        ...

    @abstractmethod
    def query_raw(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a raw SELECT query and return rows as dicts.

        Parameters
        ----------
        sql : str
            SQL statement with ``?`` placeholders.
        params : tuple | list | None
            Bound parameters for the placeholders.

        Returns
        -------
        list[dict[str, Any]]
            Result rows as column-value mappings.
        """

    @abstractmethod
    def execute(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> int:
        """
        Execute a raw DML statement (INSERT, UPDATE, DELETE, DDL).

        Parameters
        ----------
        sql : str
            SQL statement with ``?`` placeholders.
        params : tuple | list | None
            Bound parameters for the placeholders.

        Returns
        -------
        int
            Number of rows affected (for DML). May be 0 for DDL.
        """

    @abstractmethod
    def close(self) -> None:
        """Close the connection and release resources."""
        ...
