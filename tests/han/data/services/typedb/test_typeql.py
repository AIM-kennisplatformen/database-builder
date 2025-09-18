from datetime import UTC, date, datetime

from knowledgeplatformmanagement_han.data.model.document import Document
from knowledgeplatformmanagement_han.data.model.hoursbooked import HoursBooked
from knowledgeplatformmanagement_han.data.model.institution import LegalformNld
from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName
from knowledgeplatformmanagement_han.data.model.personmicrosoft365 import PersonMicrosoft365
from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.provenant import Source
from knowledgeplatformmanagement_han.data.model.subproject import Subproject
from knowledgeplatformmanagement_han.data.model.universityofappliedsciences import Universityofappliedsciences


def test_universityofappliedsciences_to_typeql() -> None:
    universityofappliedsciences = Universityofappliedsciences(
        legalform_nld=LegalformNld.stichting,
        namelike_name=NamelikeName(
            confidence=0.9,
            datetime_end_recorded=datetime(2024, 8, 14, tzinfo=UTC),
            datetime_end_updated=datetime(2024, 8, 14, tzinfo=UTC),
            value="HAN University of Applied Sciences",
            source=Source.documents,
        ),
    )
    assert universityofappliedsciences.to_typeql() == (
        'insert $namelike-name "HAN University of Applied Sciences" isa namelike-name,'
        " has confidence 0.9,"
        " has datetime-end-recorded 2024-08-14T00:00:00.000,"
        " has datetime-end-updated 2024-08-14T00:00:00.000,"
        ' has source "documents";\n'
        "$_ isa universityofappliedsciences,"
        ' has legalform-nld "stichting",'
        " has namelike-name $namelike-name;\n"
    )


def test_universityofappliedsciences_to_str() -> None:
    universityofappliedsciences = Universityofappliedsciences(
        legalform_nld=LegalformNld.stichting,
        namelike_name=NamelikeName(
            confidence=0.9,
            datetime_end_recorded=datetime(2024, 8, 14, tzinfo=UTC),
            datetime_end_updated=datetime(2024, 8, 14, tzinfo=UTC),
            value="HAN University of Applied Sciences",
            source=Source.documents,
        ),
    )
    assert str(universityofappliedsciences) == (
        "Some university of applied sciences exists, with Dutch legal form ‘stichting’, with name (value "
        "‘HAN University of Applied Sciences’, confidence of veracity ‘0.9’, timestamp of record ‘2024-08-14 "
        "00:00:00+00:00’, timestamp of record update ‘2024-08-14 00:00:00+00:00’, source ‘documents’)."
    )


def test_document_to_str() -> None:
    document = Document(
        hashvalue="123456",
        namelike_name="Test document",
    )
    assert str(document) == "Some document exists, with integer hash value ‘123456’, with name ‘Test document’."


def test_personmicrosoft365_to_typeql() -> None:
    personmicrosoft365 = PersonMicrosoft365(
        address_email="invalid@localhost.localdomain",
        namelike_last="Doe",
        namelike_first="John",
    )
    assert personmicrosoft365.to_typeql() == (
        "insert $_ isa person,"
        ' has address-email "invalid@localhost.localdomain",'
        ' has namelike-first "John",'
        ' has namelike-last "Doe";\n'
    )


def test_personmicrosoft365_to_str() -> None:
    personmicrosoft365 = PersonMicrosoft365(
        address_email="invalid@localhost.localdomain",
        namelike_last="Doe",
        namelike_first="John",
    )
    assert str(personmicrosoft365) == (
        "Some person in HAN’s Microsoft 365 tenant exists, with e-mail address ‘invalid@localhost.localdomain’, with "
        "first name ‘John’, with last name ‘Doe’."
    )


def test_hoursbooked_to_typeql() -> None:
    personubwfris = PersonUbwfris(
        address_email="test@localhost.localdomain",
        namelike_id_employee="123",
        namelike_last="Doe",
        namelike_first="John",
    )
    subproject = Subproject(
        budget=None,
        date_event_end=date(2024, 3, 19),
        date_event_start=date(2024, 3, 19),
        namelike_id_ubw="ÌD37966-185",
        namelike_id_ubwcostcentre="650787",
        namelike_name=NamelikeName(
            confidence=0.1,
            datetime_end_recorded=datetime(2024, 8, 14, tzinfo=UTC),
            datetime_end_updated=datetime(2024, 8, 14, tzinfo=UTC),
            value="rVlZfixZpIoocbqmdHiieKeRjkyINEhDPxsyZdXOudGxclCjuDHnwfuseelyRcbXYGFFHVgwajIy",
            source=Source.ubwfris,
        ),
        projectclassifier_financial="intern-declarabel",
        projectclassifier_status="ongoing",
    )
    hoursbooked = HoursBooked(
        billable=True,
        charges_hours=subproject.to_key(),
        books_hours=personubwfris.to_key(),
        date_event_registration=date(2024, 8, 14),
        timesheets_hours=1.0,
    )
    assert hoursbooked.to_typeql() == (
        "match $var1 isa subproject,"
        ' has namelike-id-ubw "ÌD37966-185";\n'
        "$var4 isa person,"
        ' has namelike-id-employee "123";\n'
        "insert $_ (charges-hours: $var1, books-hours: $var4) isa hours-booked,"
        " has billable true,"
        " has date-event-registration 2024-08-14,"
        " has timesheets-hours 1.0;\n"
    )


def test_hoursbooked_to_str() -> None:
    personubwfris = PersonUbwfris(
        address_email="test@localhost.localdomain",
        namelike_id_employee="123",
        namelike_last="Doe",
        namelike_first="John",
    )
    assert str(personubwfris) == (
        "Some person in UBW FRIS exists, with e-mail address ‘test@localhost.localdomain’, with first name ‘John’, "
        "with last name ‘Doe’, with UBW FRIS person ID ‘123’."
    )
    subproject = Subproject(
        budget=None,
        date_event_end=date(2024, 3, 19),
        date_event_start=date(2024, 3, 19),
        namelike_id_ubw="ÌD37966-185",
        namelike_id_ubwcostcentre="650787",
        namelike_name=NamelikeName(
            confidence=0.1,
            datetime_end_recorded=datetime(2024, 8, 14, tzinfo=UTC),
            datetime_end_updated=datetime(2024, 8, 14, tzinfo=UTC),
            value="rVlZfixZpIoocbqmdHiieKeRjkyINEhDPxsyZdXOudGxclCjuDHnwfuseelyRcbXYGFFHVgwajIy",
            source=Source.ubwfris,
        ),
        projectclassifier_financial="intern-declarabel",
        projectclassifier_status="ongoing",
    )
    assert str(subproject) == (
        "Some subproject in UBW FRIS exists, with project end date ‘2024-03-19’, with project start date ‘2024-03-19’, "
        "with UBW FRIS cost centre ‘650787’, with UBW FRIS project ID ‘ÌD37966-185’, with name (value "
        "‘rVlZfixZpIoocbqmdHiieKeRjkyINEhDPxsyZdXOudGxclCjuDHnwfuseelyRcbXYGFFHVgwajIy’, confidence of veracity "
        "‘0.1’, timestamp of record ‘2024-08-14 00:00:00+00:00’, timestamp of record update "
        "‘2024-08-14 00:00:00+00:00’, source ‘ubwfris’), with UBW FRIS financial classifier ‘intern-declarabel’, with "
        "UBW FRIS status classifier ‘ongoing’."
    )
    hoursbooked = HoursBooked(
        billable=True,
        charges_hours=subproject.to_key(),
        books_hours=personubwfris.to_key(),
        date_event_registration=date(2024, 8, 14),
        timesheets_hours=1.0,
    )
    assert str(hoursbooked) == (
        "Some hours booked relation exists, with billable hours ‘True’, with role subproject in UBW FRIS uniquely "
        "identified by its UBW FRIS project ID ‘ÌD37966-185’, with UBW FRIS registration date ‘2024-08-14’, with "
        "amount of hours ‘1.0’, with role person in UBW FRIS uniquely identified by its UBW FRIS person ID ‘123’."
    )
