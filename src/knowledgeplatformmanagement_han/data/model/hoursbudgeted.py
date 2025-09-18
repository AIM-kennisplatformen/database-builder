from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.timesheet import Timesheet


class HoursBudgeted(Timesheet):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="hours budgeted")
    budgets_hours: Key[PersonUbwfris] = Field(title="budgets hours")
