from contextvars import ContextVar
from types import TracebackType
from typing import Final

from typedb.driver import TypeDB, TypeDBDriver

from knowledgeplatformmanagement_generic.data.services import Dataaccessor
from knowledgeplatformmanagement_generic.data.services.typedb.connection_typedb import ConnectionTypedb
from knowledgeplatformmanagement_generic.settings import Configuration

_typedbdriver: ContextVar[TypeDBDriver] = ContextVar("typedbdriver")


class DataaccessorTypedb(Dataaccessor[ConnectionTypedb]):
    def __init__(
        self,
        *,
        configuration: Configuration,
    ) -> None:
        self.configuration: Final[Configuration] = configuration

    async def __aenter__(self) -> ConnectionTypedb:
        # TODO: TypeDB isn't well-designed, in that the driver object is invalidated when a database has been deleted,
        # rather than distinguishing an connection from a driver or connection pool. Therefore a new driver object needs
        # to be constructed for every connection.
        _typedbdriver.set(
            TypeDB.core_driver(
                address=f"{self.configuration.address_typedb!s}:{self.configuration.port_typedb}",
            ),
        )
        return ConnectionTypedb(
            configuration=self.configuration,
            typedbdriver=_typedbdriver.get(),
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        typedbdriver = _typedbdriver.get()
        typedbdriver.close()
        del typedbdriver
