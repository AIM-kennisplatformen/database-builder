from abc import ABC, abstractmethod
from types import TracebackType


class Dataaccessor[T](ABC):
    @abstractmethod
    async def __aenter__(self) -> T: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
