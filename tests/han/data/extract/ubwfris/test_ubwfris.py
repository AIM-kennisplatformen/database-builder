from collections import ChainMap, Counter
from datetime import UTC, date, datetime
from typing import IO
from uuid import uuid4

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pytest import mark

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.dao.dataqualityissue import Dataqualityissue, Dataqualityissues
from knowledgeplatformmanagement_han.data.extract.ubwfris import Ubwfris
from knowledgeplatformmanagement_han.data.model.hoursbudgeted import HoursBudgeted
from knowledgeplatformmanagement_han.data.model.hoursprojected import HoursProjected
from knowledgeplatformmanagement_han.data.model.hoursremaining import HoursRemaining
from knowledgeplatformmanagement_han.data.model.namelike_name import NamelikeName
from knowledgeplatformmanagement_han.data.model.operationalproject import Operationalproject
from knowledgeplatformmanagement_han.data.model.personubwfris import PersonUbwfris
from knowledgeplatformmanagement_han.data.model.provenant import Source

from . import (
    data_test_timesheets_rha025a_id_to_person,
    data_test_timesheets_rha025a_id_to_projectlike,
    data_test_timesheets_rha025a_timesheets,
)


# async def _load_ubwfris(
#     *,
#     datalayer: Datalayer,
#     format_worksheet: str,
#     name_worksheet_timesheets: str,
#     file_workbook: IO[bytes],
# ) -> None:
#     ubwfris = Ubwfris(datasink=datalayer.datasinks.ubwfris)
#     uuid = uuid4()
#     await ubwfris.load_worksheet(
#         file_workbook=file_workbook,
#         format_worksheet=format_worksheet,
#         name_worksheet=name_worksheet_timesheets,
#         uuid=uuid,
#     )
#     await datalayer.persist()


# @mark.anyio(scope="module")
# @mark.slow(reason="Commits large data into TypeDB Core server.")
# @mark.xdist_group(name="ubwfris")
# async def test_timesheets_ib630_synthetic(
#     datalayer: Datalayer,
#     file_workbook_ib630_withoutbooked: IO[bytes],
# ) -> None:
#     await _load_ubwfris(
#         datalayer=datalayer,
#         file_workbook=file_workbook_ib630_withoutbooked,
#         format_worksheet="IB630_without_booked",
#         name_worksheet_timesheets="IBReport 629",
#     )
#     assert datalayer.datasinks.ubwfris.id_to_personubwfris == {
#         "999-Adfas afdAA": PersonUbwfris(
#             address_email="adfas.afdaa@han.nl",
#             employmentcontract_ftepercentage=None,
#             namelike_first="Adfas",
#             namelike_id_employee="999-Adfas afdAA",
#             namelike_id_ubwcostcentre=None,
#             namelike_last="afdAA",
#         ),
#     }
#     id_to_projectlike_expected = ChainMap(
#         {},
#         {},
#         {},
#         {
#             "ÌD1123": Operationalproject(
#                 budget=None,
#                 date_event_end=date(2024, 11, 1),
#                 date_event_start=date(2024, 11, 1),
#                 namelike_id_ubw="ÌD1123",
#                 namelike_id_ubwcostcentre="120014",
#                 namelike_name=NamelikeName(
#                     confidence=0.1,
#                     datetime_end_recorded=datetime(1, 1, 1, tzinfo=UTC),
#                     datetime_end_updated=datetime(1, 1, 1, tzinfo=UTC),
#                     value="dj33289jdhceuwijcsiova dSDS # 23 asaas",
#                     source=Source.ubwfris,
#                 ),
#                 projectclassifier_financial="intern-declarabel",
#                 projectclassifier_status=None,
#             ),
#         },
#         {},
#         {},
#         {},
#     )
#     assert datalayer.datasinks.ubwfris.id_to_projectlike == id_to_projectlike_expected
#     assert datalayer.datasinks.ubwfris.id_to_subproject == {}
#     assert datalayer.datasinks.ubwfris.timesheets == [
#         HoursBudgeted(
#             billable=False,
#             charges_hours=Key(
#                 classobject=Operationalproject,
#                 name_key="namelike_id_ubw",
#                 name_schema="operationalproject",
#                 title="operational project",
#                 title_key="UBW FRIS project ID",
#                 value_key="ÌD1123",
#             ),
#             date_event_registration=date(2024, 11, 1),
#             timesheets_hours=12.56,
#             budgets_hours=Key(
#                 classobject=PersonUbwfris,
#                 name_key="namelike_id_employee",
#                 name_schema=PersonUbwfris.to_typeql_name_schema(),
#                 title="person in UBW FRIS",
#                 title_key="UBW FRIS person ID",
#                 value_key="999-Adfas afdAA",
#             ),
#         ),
#         HoursProjected(
#             billable=False,
#             charges_hours=Key(
#                 classobject=Operationalproject,
#                 name_key="namelike_id_ubw",
#                 name_schema="operationalproject",
#                 title="operational project",
#                 title_key="UBW FRIS project ID",
#                 value_key="ÌD1123",
#             ),
#             date_event_registration=date(2024, 11, 1),
#             timesheets_hours=12.56,
#             projects_hours=Key(
#                 classobject=PersonUbwfris,
#                 name_key="namelike_id_employee",
#                 name_schema=PersonUbwfris.to_typeql_name_schema(),
#                 title="person in UBW FRIS",
#                 title_key="UBW FRIS person ID",
#                 value_key="999-Adfas afdAA",
#             ),
#         ),
#         HoursRemaining(
#             billable=False,
#             charges_hours=Key(
#                 classobject=Operationalproject,
#                 name_key="namelike_id_ubw",
#                 name_schema="operationalproject",
#                 title="operational project",
#                 title_key="UBW FRIS project ID",
#                 value_key="ÌD1123",
#             ),
#             date_event_registration=date(2024, 11, 1),
#             timesheets_hours=-18.44,
#             remains_hours=Key(
#                 classobject=PersonUbwfris,
#                 name_key="namelike_id_employee",
#                 name_schema=PersonUbwfris.to_typeql_name_schema(),
#                 title="person in UBW FRIS",
#                 title_key="UBW FRIS person ID",
#                 value_key="999-Adfas afdAA",
#             ),
#         ),
#     ]


# @mark.anyio(scope="module")
# @mark.slow(reason="Commits large data into TypeDB Core server.")
# @mark.xdist_group(name="ubwfris")
# async def test_timesheets_rha025a_synthetic(
#     *,
#     datalayer: Datalayer,
#     file_workbook_rha025a: IO[bytes],
# ) -> None:
#     await _load_ubwfris(
#         datalayer=datalayer,
#         file_workbook=file_workbook_rha025a,
#         format_worksheet="RHA025A",
#         name_worksheet_timesheets="Sheet1",
#     )
#     assert datalayer.datasinks.ubwfris.id_to_personubwfris == data_test_timesheets_rha025a_id_to_person.id_to_person
#     assert (
#         datalayer.datasinks.ubwfris.id_to_projectlike
#         == data_test_timesheets_rha025a_id_to_projectlike.id_to_projectlike
#     )
#     assert datalayer.datasinks.ubwfris.timesheets == data_test_timesheets_rha025a_timesheets.timesheets
#     dataqualityissues_actual = Dataqualityissues.model_validate(
#         next(iter(datalayer.datasinks.ubwfris.uuid_to_dataqualityissues.values())),
#     )
#     dataqualityissues_expected = Dataqualityissues.model_validate(
#         [
#             Dataqualityissue(
#                 attributes=("projecttypecode",),
#                 index_row=2,
#                 input=None,
#                 message="Input should be a valid string",
#                 type="string_type",
#             ),
#         ],
#         strict=True,
#     )
#     assert dataqualityissues_expected == dataqualityissues_actual


# @mark.anyio(scope="module")
# @mark.sensitive(reason="The dataset is real and not sanitized.")
# @mark.slow(reason="Commits large data into TypeDB Core server.")
# @mark.xdist_group(name="ubwfris")
# async def test_timesheets_rha025a_real(
#     *,
#     datalayer: Datalayer,
#     file_workbook_rha025a_real: IO[bytes],
# ) -> None:
#     await _load_ubwfris(
#         datalayer=datalayer,
#         file_workbook=file_workbook_rha025a_real,
#         format_worksheet="RHA025A",
#         name_worksheet_timesheets="Urenstaten Bron",
#     )
#     assert len(datalayer.datasinks.ubwfris.id_to_personubwfris) == 65  # noqa: PLR2004
#     assert len(datalayer.datasinks.ubwfris.id_to_projectlike) == 205  # noqa: PLR2004
#     assert len(datalayer.datasinks.ubwfris.id_to_subproject) == 136  # noqa: PLR2004
#     assert len(datalayer.datasinks.ubwfris.timesheets) == 8756  # noqa: PLR2004
#     projectclassifier_financial_to_count = Counter(
#         projectlike.projectclassifier_financial
#         for projectlike in datalayer.datasinks.ubwfris.id_to_projectlike.values()
#     )
#     assert projectclassifier_financial_to_count == Counter(
#         {
#             "contractonderwijs": 2,
#             "intern-declarabel": 111,
#             "marktactiviteiten": 11,
#             "subsidieprojecten": 81,
#         },
#     )


# @mark.anyio(scope="module")
# @mark.sensitive(reason="The dataset is real and not sanitized.")
# @mark.slow(reason="Commits large data into TypeDB Core server.")
# @mark.xdist_group(name="ubwfris")
# async def test_timesheets_ib630_real(
#     *,
#     datalayer: Datalayer,
#     file_workbook_ib630_withoutbooked_real: IO[bytes],
# ) -> None:
#     await _load_ubwfris(
#         datalayer=datalayer,
#         file_workbook=file_workbook_ib630_withoutbooked_real,
#         format_worksheet="IB630",
#         name_worksheet_timesheets="IBReport 629",
#     )
#     assert len(datalayer.datasinks.ubwfris.id_to_personubwfris) == 23  # noqa: PLR2004
#     assert len(datalayer.datasinks.ubwfris.id_to_projectlike) == 68  # noqa: PLR2004
#     assert len(datalayer.datasinks.ubwfris.id_to_subproject) == 0
#     assert len(datalayer.datasinks.ubwfris.timesheets) == 27192  # noqa: PLR2004
#     projectclassifier_financial_to_count = Counter(
#         projectlike.projectclassifier_financial
#         for projectlike in datalayer.datasinks.ubwfris.id_to_projectlike.values()
#     )
#     assert projectclassifier_financial_to_count == Counter(
#         {"intern-declarabel": 23, "subsidieprojecten": 39, "marktactiviteiten": 4, "contractonderwijs": 2},
#     )
