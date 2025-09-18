from asapi import Injected
from fastapi import APIRouter, Response, status

from knowledgeplatformmanagement_han.data.dao.datalayer import Datalayer

router = APIRouter()


@router.post("/clear")
async def clear(
    *,
    datalayer: Injected[Datalayer],
) -> Response:
    await datalayer.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/init")
async def init(
    *,
    datalayer: Injected[Datalayer],
) -> Response:
    await datalayer.init()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/persist")
async def persist(
    *,
    datalayer: Injected[Datalayer],
) -> Response:
    await datalayer.persist()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
