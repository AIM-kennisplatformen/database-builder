from collections.abc import AsyncGenerator, Iterable
from typing import Any, Final

from anyio import Path
from loguru import logger
from typedb.driver import SessionType, TransactionType, TypeDBDriver

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing
from knowledgeplatformmanagement_generic.settings import Configuration


class ConnectionTypedb:
    def __init__(self, *, configuration: Configuration, typedbdriver: TypeDBDriver) -> None:
        self._typedbdriver: Final[TypeDBDriver] = typedbdriver
        self.configuration: Final[Configuration] = configuration

    def create_database(self) -> None:
        if self._typedbdriver is not None:
            self._typedbdriver.databases.create(self.configuration.name_database)

    async def create_schema(self, *, path_file_schema: Path) -> None:
        assert self._typedbdriver is not None
        with (
            self._typedbdriver.session(
                database_name=self.configuration.name_database,
                session_type=SessionType.SCHEMA,
            ) as session,
            session.transaction(TransactionType.WRITE) as transaction_write,
        ):
            async with await path_file_schema.open(
                encoding="utf-8",
            ) as file:
                query = await file.read()
                transaction_write.query.define(query)
                transaction_write.commit()

    def delete_database(self) -> None:
        if self._typedbdriver is not None:
            self._typedbdriver.databases.get(self.configuration.name_database).delete()

    async def fetch(
        self,
        *,
        path_file_query: Path,
        type_transaction: TransactionType = TransactionType.READ,
    ) -> AsyncGenerator[dict[str, Any]]:
        query = await path_file_query.read_text(encoding="utf-8")
        with (
            self._typedbdriver.session(
                database_name=self.configuration.name_database,
                session_type=SessionType.DATA,
            ) as session,
            session.transaction(type_transaction) as transaction,
        ):
            for result in transaction.query.fetch(query):
                yield result

    async def insert_typeqlthings(self, *, typeqlthings: Iterable[TypeqlThing]) -> None:
        with (
            self._typedbdriver.session(
                database_name=self.configuration.name_database,
                session_type=SessionType.DATA,
            ) as session,
            session.transaction(TransactionType.WRITE) as transaction_write,
        ):
            for thing in typeqlthings:
                query = thing.to_typeql()
                logger.trace("{}", query)
                transaction_write.query.insert(query)
            transaction_write.commit()
