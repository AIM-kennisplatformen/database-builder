from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.timesheet import Timesheet


class HoursBooked(Timesheet):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="hours booked")
    books_hours: Key[PersonUbwfris] = Field(title="books hours")
