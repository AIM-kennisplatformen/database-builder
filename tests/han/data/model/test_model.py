from datetime import UTC, date, datetime

from knowledgeplatformmanagement_han.data.model.hoursbooked import HoursBooked
from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName
from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.provenant import Source
from knowledgeplatformmanagement_han.data.model.subproject import Subproject


def test_model() -> None:
    person = PersonUbwfris(
        address_email="test@localhost.localdomain",
        namelike_id_employee="79491737",
        namelike_first="John",
        namelike_last="Doe",
    )
    subproject = Subproject(
        namelike_id_ubwcostcentre="1954989",
        date_event_end=date(1, 1, 1),
        date_event_start=date(1, 1, 1),
        namelike_id_ubw="SU1234-101",
        namelike_name=NamelikeName(
            confidence=0.1,
            datetime_end_recorded=datetime(1, 1, 1, tzinfo=UTC),
            datetime_end_updated=datetime(1, 1, 1, tzinfo=UTC),
            source=Source.ubwfris,
            value="Subproject",
        ),
        projectclassifier_financial="subsidieprojecten",
        projectclassifier_status="ongoing",
    )
    books_hours = person.to_key()
    charges_hours = subproject.to_key()
    hoursbooked = HoursBooked(
        billable=True,
        books_hours=books_hours,
        charges_hours=charges_hours,
        date_event_registration=date(1, 1, 1),
        timesheets_hours=1.0,
    )
    assert len(hoursbooked.to_typeql()) > 1
