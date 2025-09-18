from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.timesheet import Timesheet


class HoursRemaining(Timesheet):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="hours remaining of budget")
    remains_hours: Key[PersonUbwfris] = Field(title="remains hours")
