from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.person import Person


class PersonMicrosoft365(Person):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="person in HAN’s Microsoft 365 tenant")

    interests: list[str] | None = Field(default=None, title="interests")
    responsibilities: list[str] | None = Field(default=None, title="responsibilities")
    schools: list[str] | None = Field(default=None, title="schools")
    skills: list[str] | None = Field(default=None, title="skills")
