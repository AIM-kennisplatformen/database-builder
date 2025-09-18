from enum import StrEnum, auto, unique

from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.provenant import ProvenantString


@unique
class Keyareas(StrEnum):
    schoon = auto()
    slim = auto()
    sociaal = auto()


class Keyarea(ProvenantString):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="HAN key area")
    value: Keyareas = Field(title="value")
