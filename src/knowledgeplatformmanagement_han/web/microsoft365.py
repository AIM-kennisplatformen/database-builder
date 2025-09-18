from asapi import Injected
from fastapi import APIRouter, HTTPException, Response, status
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from pydantic import RootModel

from knowledgeplatformmanagement_han.data.extract.microsoft365 import Microsoft365
from knowledgeplatformmanagement_han.data.model.personmicrosoft365 import PersonMicrosoft365

GetHanemployees = RootModel[list[PersonMicrosoft365]]

router = APIRouter(prefix="/microsoft365")


@router.get("/get_han_employees")
async def get_han_employees(
    *,
    microsoft365: Injected[Microsoft365],
) -> Response:
    if microsoft365._microsoft365_scopes_user:
        try:
            await microsoft365.get_han_employees()
        except ODataError as exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fault during Microsoft 365 Graph API call.",
            ) from exception
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Microsoft 365 functionality is disabled.")
