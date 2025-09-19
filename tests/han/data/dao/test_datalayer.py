from collections.abc import Sequence
from datetime import date
from typing import Any

from pytest import mark, param, raises

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.extract.ubwfris import ExportPowerbiTimesheet


# @mark.anyio(scope="module")
# @mark.parametrize(
#     "exportpowerbitimesheets,exportpowerbitimesheets_expected",
#     [
#         param(
#             [
#                 {
#                     "timesheet": {
#                         "billable": [{"value": True}],
#                         "date_event_registration": [{"value": "2024-07-24T00:00:00"}],
#                         "timesheets_hours": [{"value": 8.0}],
#                         "type": {"label": "booked"},
#                     },
#                     "person": {"namelike_id_employee": [{"value": "123"}]},
#                     "subproject": {
#                         "namelike_id_ubw": [{"value": "IN12345"}],
#                         "projectclassifier_financial": [{"value": "intern-declarabel"}],
#                         "namelike_name": [{"value": "Test Project"}],
#                     },
#                 },
#             ],
#             [
#                 ExportPowerbiTimesheet(
#                     billable=True,
#                     date=date(2024, 7, 24),
#                     hours_type="booked",
#                     hours=8.0,
#                     namelike_id_employee="123",
#                     namelike_id_ubw="IN12345",
#                     namelike_name="Test Project",
#                     project_type_name_powerbi="Intern Declarabel",
#                 ),
#             ],
#             id="happy_path_single_exportpowerbitimesheet",
#         ),
#         param(
#             [
#                 {
#                     "timesheet": {
#                         "billable": [{"value": True}],
#                         "date_event_registration": [{"value": "2024-08-15T00:00:00"}],
#                         "timesheets_hours": [{"value": 4.0}],
#                         "type": {"label": "budgeted"},
#                     },
#                     "person": {"namelike_id_employee": [{"value": "456"}]},
#                     "subproject": {
#                         "namelike_id_ubw": [{"value": "OM98765"}],
#                         "projectclassifier_financial": [{"value": "onderzoekmarkt"}],
#                         "namelike_name": [{"value": "Another Project"}],
#                     },
#                 },
#                 {
#                     "timesheet": {
#                         "billable": [{"value": True}],
#                         "date_event_registration": [{"value": "2024-09-01T00:00:00"}],
#                         "timesheets_hours": [{"value": 12.0}],
#                         "type": {"label": "projected"},
#                     },
#                     "person": {"namelike_id_employee": [{"value": "789"}]},
#                     "subproject": {
#                         "namelike_id_ubw": [{"value": "CO54321"}],
#                         "projectclassifier_financial": [{"value": "contractonderwijs"}],
#                         "namelike_name": [{"value": "Third Project"}],
#                     },
#                 },
#             ],
#             [
#                 ExportPowerbiTimesheet(
#                     billable=True,
#                     date=date(2024, 8, 15),
#                     hours_type="budgeted",
#                     hours=4.0,
#                     namelike_id_employee="456",
#                     namelike_id_ubw="OM98765",
#                     namelike_name="Another Project",
#                     project_type_name_powerbi="Onderzoek Markt",
#                 ),
#                 ExportPowerbiTimesheet(
#                     billable=True,
#                     date=date(2024, 9, 1),
#                     hours_type="projected",
#                     hours=12.0,
#                     namelike_id_employee="789",
#                     namelike_id_ubw="CO54321",
#                     namelike_name="Third Project",
#                     project_type_name_powerbi="Contractonderwijs",
#                 ),
#             ],
#             id="happy_path_multiple_exportpowerbitimesheets",
#         ),
#         param(
#             [],
#             [],
#             id="edge_case_empty_exportpowerbitimesheets",
#         ),
#     ],
# )
# async def test_export_powerbi_timesheets(
#     *,
#     exportpowerbitimesheets: Sequence[dict[str, Any]],
#     exportpowerbitimesheets_expected: Sequence[ExportPowerbiTimesheet],
#     datalayer: Datalayer,
# ) -> None:
#     exportpowerbitimesheets_deserialized = [
#         datalayer._export_powerbi_timesheet(exportpowerbitimesheet)
#         for exportpowerbitimesheet in exportpowerbitimesheets
#     ]
#     assert exportpowerbitimesheets_deserialized == exportpowerbitimesheets_expected


# @mark.anyio(scope="module")
# @mark.parametrize(
#     "exportpowerbitimesheets,exception_expected",
#     [
#         param(
#             [
#                 {
#                     "subproject": {
#                         "namelike_id_ubw": [{"value": "IN12345"}],
#                         "projectclassifier_financial": [{"value": "invalid"}],
#                         "namelike_name": [{"value": "Invalid Project"}],
#                     },
#                     "timesheet": {
#                         "date_event_registration": [{"value": "2024-10-26T00:00:00"}],
#                         "timesheets_hours": [{"value": 5.0}],
#                         "type": {"label": "remaining"},
#                     },
#                     "person": {"namelike_id_employee": [{"value": "999"}]},
#                 },
#             ],
#             KeyError,
#             id="error_case_invalid_project_type",
#         ),
#     ],
# )
# async def test_export_powerbi_timesheets_exception(
#     *,
#     datalayer: Datalayer,
#     exception_expected: type[ValueError],
#     exportpowerbitimesheets: list[dict[str, Any]],
# ) -> None:
#     with raises(exception_expected):
#         _exportpowerbitimesheets_deserialized = [
#             datalayer._export_powerbi_timesheet(exportpowerbitimesheet)
#             for exportpowerbitimesheet in exportpowerbitimesheets
#         ]
