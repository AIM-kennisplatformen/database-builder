from datetime import date

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key, TypeqlThingRelation
from pydantic import ConfigDict, Field, FiniteFloat

from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike


class Timesheet(TypeqlThingRelation):
    model_config = ConfigDict(title="UBW FRIS timesheet")
    billable: bool = Field(title="billable hours")
    charges_hours: Key[Projectlike] = Field(title="charges hours")
    date_event_registration: date = Field(title="UBW FRIS registration date")
    timesheets_hours: FiniteFloat = Field(title="amount of hours")
