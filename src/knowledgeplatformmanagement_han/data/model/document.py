from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingEntity
from pydantic import ConfigDict, Field, StringConstraints


class Document(TypeqlThingEntity):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="document")
    hashvalue: Annotated[str, "key"] = Field(title="integer hash value")
    namelike_name: Annotated[str, StringConstraints(min_length=1)] = Field(title="name")
