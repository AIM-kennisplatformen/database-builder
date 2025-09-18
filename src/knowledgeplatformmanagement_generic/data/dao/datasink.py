from abc import abstractmethod
from collections.abc import Generator

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing


# This declares a slim interface.
# pylint: disable-next=too-few-public-methods
class Datasink:
    @abstractmethod
    def populate(self) -> Generator[TypeqlThing, None]: ...
