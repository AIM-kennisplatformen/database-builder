from abc import ABC, abstractmethod
from typing import Any


class AbstractRelationalStore(ABC):
    """
    Abstract interface for a relational data store.

    Provides primitive operations for executing queries, committing
    transactions, and managing the lifecycle. Implementations may
    use SQLite, PostgreSQL, or any other relational backend.
    """

    @abstractmethod
    def execute(self, sql: str, params: tuple | list | None = None) -> Any:
        """
        Execute a single SQL statement and return the cursor.

        Parameters
        ----------
        sql : str
            SQL statement, optionally with ``?`` placeholders.
        params : tuple | list | None
            Bound parameters for the placeholders.

        Returns
        -------
        Any
            A cursor-like object that supports ``fetchone()``,
            ``fetchall()``, and ``rowcount``.
        """
        ...

    @abstractmethod
    def executemany(self, sql: str, rows: list[tuple]) -> None:
        """
        Execute the same SQL statement for every row in ``rows``.

        Parameters
        ----------
        sql : str
            SQL statement with ``?`` placeholders.
        rows : list[tuple]
            Each tuple provides the parameter values for one execution.
        """
        ...

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def cursor(self) -> Any:
        """
        Return a new cursor object.

        Consumers should prefer ``execute()`` over ``cursor()``
        whenever possible, because ``execute()`` may include
        additional guarantees such as automatic retries.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the connection and release resources."""
        ...
