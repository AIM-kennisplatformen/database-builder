from typing import Annotated

from annotated_types import Ge, Le
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.namelike_id_employee import NamelikeIdEmployee
from knowledgeplatformmanagement_han.data.model.namelike_id_ubwcostcentre import NamelikeIdUbwcostcentre
from knowledgeplatformmanagement_han.data.model.person import Person


class PersonUbwfris(Person):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="person in UBW FRIS")

    employmentcontract_ftepercentage: Annotated[int, Ge(0), Le(100)] | None = Field(
        default=None,
        title="employment contract FTE %",
    )
    namelike_id_employee: Annotated[NamelikeIdEmployee, "key"] = Field(title="UBW FRIS person ID")
    namelike_id_ubwcostcentre: NamelikeIdUbwcostcentre | None = Field(default=None, title="UBW FRIS cost centre ID")
