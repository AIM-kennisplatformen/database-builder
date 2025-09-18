from typing import Final

from knowledgeplatformmanagement_generic.data.services.llm import Llm


# TODO: Add methods.
# pylint: disable-next=too-few-public-methods
class ConnectionLlm:
    def __init__(self, *, llm: Llm) -> None:
        self._llm: Final[Llm] = llm
