from typing import Annotated
from uuid import uuid4

from asapi import FromForm, FromPath, Injected
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status

# Pydantic can't handle imports under TYPE_CHECKING.
from fastapi.responses import StreamingResponse
from knowledgeplatformmanagement_generic.web import stream_json_list
from pydantic import UUID4, BaseModel

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer
from knowledgeplatformmanagement_han.data.dao.dataqualityissue import Dataqualityissues
from knowledgeplatformmanagement_han.data.extract.ubwfris import (
    ExportPowerbiPerson,
    ExportPowerbiTimesheet,
    TimesheetsAlreadyloadedError,
    TimesheetsFormatInvalidError,
    TimesheetsWorksheetUnavailableError,
    Ubwfris,
)
from knowledgeplatformmanagement_han.settings import Configuration

router = APIRouter(
    prefix="/timesheets",
)


class ResponseUuid(BaseModel, frozen=True):
    uuid: UUID4


@router.post("/load")
async def timesheets_load(
    *,
    configuration: Injected[Configuration],
    name_worksheet: FromForm[str],
    format_worksheet: FromForm[str],
    file_workbook: FromForm[
        Annotated[
            UploadFile,
            File(
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ]
    ],
    ubwfris: Injected[Ubwfris],
) -> ResponseUuid:
    # TODO: (infosec) Replace with middleware. This will trust untrusted input from the client, and will download the
    # file in full first.
    # Limit file uploads of workbooks. See: https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload
    if file_workbook.size and file_workbook.size < configuration.size_max_workbook and file_workbook.content_type:
        try:
            uuid = await ubwfris.load_worksheet(
                file_workbook=file_workbook.file,
                format_worksheet=format_worksheet,
                name_worksheet=name_worksheet,
                uuid=uuid4(),
            )
        except (TimesheetsFormatInvalidError, TimesheetsWorksheetUnavailableError) as exception:
            raise HTTPException(
                detail=str(exception),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            ) from exception
        except TimesheetsAlreadyloadedError as exception:
            raise HTTPException(
                detail=str(exception),
                status_code=status.HTTP_409_CONFLICT,
            ) from exception
        return ResponseUuid(uuid=uuid)
    raise HTTPException(
        detail="One or more files had a zero or unspecified length, or incorrect content type.",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@router.delete("/delete/{uuid}")
async def delete_worksheet(*, uuid: FromPath[UUID4], ubwfris: Injected[Ubwfris]) -> Response:
    try:
        ubwfris.delete_worksheet(uuid=uuid)
    except KeyError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet (UUID {uuid}) not found.",
        ) from exception
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset")
async def reset(*, ubwfris: Injected[Ubwfris]) -> Response:
    ubwfris.reset()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dataqualityissues/{uuid}")
async def get_dataqualityissues(
    *,
    uuid: FromPath[UUID4],
    ubwfris: Injected[Ubwfris],
) -> Dataqualityissues:
    try:
        dataqualityissues = Dataqualityissues.model_validate(
            ubwfris.datasink.uuid_to_dataqualityissues[uuid],
            strict=True,
        )
    except KeyError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet (UUID {uuid}) not found.",
        ) from exception
    return dataqualityissues


@router.get("/persons_missing/{uuid}")
async def get_persons_missing(
    *,
    uuid: FromPath[UUID4],
    ubwfris: Injected[Ubwfris],
) -> list[str]:
    try:
        persons_missing = ubwfris.datasink.uuid_to_persons_missing[uuid]
    except KeyError as exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worksheet (UUID {uuid}) not found.",
        ) from exception
    return persons_missing


@router.get("/export_powerbi/timesheets", response_model=ExportPowerbiTimesheet)
async def export_powerbi_timesheets(
    *,
    datalayer: Injected[Datalayer],
) -> StreamingResponse:
    return StreamingResponse(
        content=stream_json_list(
            iterator=datalayer.export_powerbi_timesheets(),
            itemrenderer=ExportPowerbiTimesheet.model_dump_json,
        ),
        media_type="application/json",
    )


@router.get("/export_powerbi/persons", response_model=ExportPowerbiPerson)
async def export_powerbi_persons(
    *,
    datalayer: Injected[Datalayer],
) -> StreamingResponse:
    return StreamingResponse(
        content=stream_json_list(
            iterator=datalayer.export_powerbi_persons(),
            itemrenderer=ExportPowerbiPerson.model_dump_json,
        ),
        media_type="application/json",
    )
