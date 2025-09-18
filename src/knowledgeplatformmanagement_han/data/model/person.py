from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingEntity
from pydantic import ConfigDict, EmailStr, Field, StringConstraints


class Person(TypeqlThingEntity):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="person")

    # TODO: Should be a key.
    address_email: EmailStr = Field(title="e-mail address")
    namelike_first: Annotated[str, StringConstraints(min_length=1)] = Field(title="first name")
    namelike_last: Annotated[str, StringConstraints(min_length=1)] = Field(title="last name")
