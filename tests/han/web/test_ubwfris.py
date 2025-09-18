from collections.abc import Sequence
from json import load as json_load
from pathlib import Path as PathSync
from typing import IO, NamedTuple

from anyio import Path
from fastapi import status
from fastapi.testclient import TestClient
from pydantic import UUID4
from pytest import mark, param

from knowledgeplatformmanagement_han.data.dao.dataqualityissue import Dataqualityissues
from knowledgeplatformmanagement_han.data.extract.ubwfris import ExportPowerbiPersons, ExportPowerbiTimesheets

from .test_common import _persist


class FlowWorkbook(NamedTuple):
    format_worksheet: str
    name_worksheet: str
    path_file_dataqualityissues: PathSync
    path_file_persons_missing: PathSync


FLOWWORKBOOKS = (
    FlowWorkbook(
        format_worksheet="IB630_without_booked",
        name_worksheet="IBReport 629",
        path_file_dataqualityissues=(PathSync(__file__).parent / "dataqualityissues_IB630_without_booked.json").resolve(
            strict=True,
        ),
        path_file_persons_missing=(PathSync(__file__).parent / "persons_missing_IB630_without_booked.json").resolve(
            strict=True,
        ),
    ),
    FlowWorkbook(
        format_worksheet="RHA025A",
        name_worksheet="Sheet1",
        path_file_dataqualityissues=(PathSync(__file__).parent / "dataqualityissues_RHA025A.json").resolve(
            strict=True,
        ),
        path_file_persons_missing=(PathSync(__file__).parent / "persons_missing_RHA025A.json").resolve(
            strict=True,
        ),
    ),
)


def _timesheets_load(
    *,
    file_workbook_ib630_withoutbooked: IO[bytes],
    file_workbook_rha025a: IO[bytes],
    flowworkbook: FlowWorkbook,
    testclient: TestClient,
    uuid: UUID4 | None = None,
) -> UUID4:
    data = {
        "format_worksheet": flowworkbook.format_worksheet,
        "name_worksheet": flowworkbook.name_worksheet,
    }
    if uuid:
        data["uuid"] = str(uuid)
    response = testclient.post(
        data=data,
        files={
            "file_workbook": (
                f"{flowworkbook.format_worksheet}.xlsx",
                (
                    file_workbook_ib630_withoutbooked
                    if flowworkbook.format_worksheet == "IB630_without_booked"
                    else file_workbook_rha025a
                ),
                "multipart/form-data",
            ),
        },
        headers={"Host": "localhost.localdomain"},
        url="/timesheets/load",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    return UUID4(response.json()["uuid"])


async def _dataqualityissues(*, path_file_dataqualityissues: Path, testclient: TestClient, uuid: UUID4) -> None:
    response = testclient.get(
        headers={"Host": "localhost.localdomain"},
        url=f"/timesheets/dataqualityissues/{uuid!s}",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    async with await path_file_dataqualityissues.open("rt") as file_dataqualityissues:
        dataqualityissues_expected: Dataqualityissues = Dataqualityissues.model_validate_json(
            await file_dataqualityissues.read(),
            strict=True,
        )
    dataqualityissues_actual = Dataqualityissues.model_validate_json(response.read(), strict=True)
    assert dataqualityissues_expected == dataqualityissues_actual


async def _persons_missing(*, path_file_persons_missing: Path, testclient: TestClient, uuid: UUID4) -> None:
    response = testclient.get(
        headers={"Host": "localhost.localdomain"},
        url=f"/timesheets/persons_missing/{uuid!s}",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    async with await path_file_persons_missing.open("rt") as file_persons_missing:
        persons_missing_expected = json_load(file_persons_missing._fp)
    persons_missing_actual = response.json()
    assert persons_missing_expected == persons_missing_actual


async def _timesheets_delete(*, testclient: TestClient, uuid: UUID4) -> None:
    response = testclient.delete(
        headers={"Host": "localhost.localdomain"},
        url=f"/timesheets/delete/{uuid!s}",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def _timesheets_reset(*, testclient: TestClient) -> None:
    response = testclient.post(
        headers={"Host": "localhost.localdomain"},
        url="/timesheets/reset",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


async def _export_powerbi_persons(*, testclient: TestClient) -> None:
    response = testclient.get(
        headers={"Host": "localhost.localdomain"},
        url="/timesheets/export_powerbi/persons",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    async with await (Path(__file__).parent / "export_powerbi_persons.json").open("rt") as file_exportpowerbipersons:
        exportpowerbipersons_expected = ExportPowerbiPersons.model_validate_json(
            await file_exportpowerbipersons.read(),
            strict=True,
        )
    exportpowerbipersons_actual = ExportPowerbiPersons.model_validate_json(response.text, strict=False)
    exportpowerbipersons_actual.root = sorted(
        exportpowerbipersons_actual.root,
        key=lambda exportpowerbipersons: (
            exportpowerbipersons.employmentcontract_ftepercentage or 0,
            exportpowerbipersons.namelike_full,
            exportpowerbipersons.namelike_id_employee,
            exportpowerbipersons.namelike_id_ubwcostcentre or "0",
        ),
    )
    assert exportpowerbipersons_expected == exportpowerbipersons_actual


async def _export_powerbi_timesheets(*, testclient: TestClient) -> None:
    response = testclient.get(
        headers={"Host": "localhost.localdomain"},
        url="/timesheets/export_powerbi/timesheets",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    async with await (Path(__file__).parent / "export_powerbi_timesheets.json").open(
        "rt",
    ) as file_exportpowerbitimesheets:
        exportpowerbitimesheets_expected = ExportPowerbiTimesheets.model_validate_json(
            await file_exportpowerbitimesheets.read(),
            strict=True,
        )
    exportpowerbitimesheets_actual = ExportPowerbiTimesheets.model_validate_json(
        response.text,
        strict=False,
    )
    exportpowerbitimesheets_actual.root = sorted(
        exportpowerbitimesheets_actual.root,
        key=lambda exportpowerbitimesheets: (
            exportpowerbitimesheets.billable,
            exportpowerbitimesheets.date,
            exportpowerbitimesheets.hours,
            exportpowerbitimesheets.hours_type,
            exportpowerbitimesheets.namelike_id_employee,
            exportpowerbitimesheets.namelike_id_ubw,
            exportpowerbitimesheets.namelike_id_employee,
            exportpowerbitimesheets.namelike_name,
            exportpowerbitimesheets.project_type_name_powerbi,
        ),
    )
    assert exportpowerbitimesheets_expected == exportpowerbitimesheets_actual


@mark.anyio(scope="module")
@mark.xdist_group(name="ubwfris")
@mark.parametrize(
    "flowworkbooks",
    [param(FLOWWORKBOOKS, id="normal"), param(tuple(reversed(FLOWWORKBOOKS)), id="reversed")],
)
async def test_timesheets(
    *,
    flowworkbooks: Sequence[FlowWorkbook],
    testclient: TestClient,
    file_workbook_rha025a: IO[bytes],
    file_workbook_ib630_withoutbooked: IO[bytes],
) -> None:
    uuid = _timesheets_load(
        flowworkbook=flowworkbooks[0],
        testclient=testclient,
        file_workbook_ib630_withoutbooked=file_workbook_ib630_withoutbooked,
        file_workbook_rha025a=file_workbook_rha025a,
    )
    uuid_2 = _timesheets_load(
        testclient=testclient,
        flowworkbook=flowworkbooks[1],
        file_workbook_ib630_withoutbooked=file_workbook_ib630_withoutbooked,
        file_workbook_rha025a=file_workbook_rha025a,
        uuid=uuid,
    )
    await _dataqualityissues(
        path_file_dataqualityissues=Path(flowworkbooks[0].path_file_dataqualityissues),
        testclient=testclient,
        uuid=uuid,
    )
    await _dataqualityissues(
        path_file_dataqualityissues=Path(flowworkbooks[1].path_file_dataqualityissues),
        testclient=testclient,
        uuid=uuid_2,
    )
    await _persons_missing(
        path_file_persons_missing=Path(flowworkbooks[0].path_file_persons_missing),
        testclient=testclient,
        uuid=uuid,
    )
    await _persons_missing(
        path_file_persons_missing=Path(flowworkbooks[1].path_file_persons_missing),
        testclient=testclient,
        uuid=uuid_2,
    )
    await _persist(testclient=testclient)
    await _timesheets_delete(testclient=testclient, uuid=uuid)
    await _timesheets_delete(testclient=testclient, uuid=uuid_2)
    await _export_powerbi_timesheets(testclient=testclient)
    await _export_powerbi_persons(testclient=testclient)
    await _timesheets_reset(testclient=testclient)
