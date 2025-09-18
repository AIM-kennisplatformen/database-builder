from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingEntity
from pydantic import ConfigDict, Field, StringConstraints

from knowledgeplatformmanagement_han.data.model.namelike_id_school import NamelikeIdSchool


class School(TypeqlThingEntity):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="HAN school")
    namelike_id_school: Annotated[NamelikeIdSchool, "key"] = Field(title="UBW FRIS HAN school ID")
    namelike_department: Annotated[str, StringConstraints(min_length=1)] = Field(title="HAN main department name")
