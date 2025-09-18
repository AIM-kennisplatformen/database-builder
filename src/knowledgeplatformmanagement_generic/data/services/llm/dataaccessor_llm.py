from types import TracebackType
from typing import Final

from openai import OpenAI

from knowledgeplatformmanagement_generic.data.services import Dataaccessor
from knowledgeplatformmanagement_generic.data.services.llm import Llm
from knowledgeplatformmanagement_generic.data.services.llm.connection_llm import ConnectionLlm
from knowledgeplatformmanagement_generic.settings import Configuration


class DataaccessorLlm(Dataaccessor[ConnectionLlm]):
    def __init__(
        self,
        *,
        configuration: Configuration,
        openai: OpenAI,
    ) -> None:
        self.configuration: Final[Configuration] = configuration
        self._llm: Final[Llm] = Llm(configuration=configuration, openai=openai)

    async def __aenter__(self) -> ConnectionLlm:
        return ConnectionLlm(llm=self._llm)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass
