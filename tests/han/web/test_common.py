from fastapi import status
from fastapi.testclient import TestClient


async def _persist(*, testclient: TestClient) -> None:
    response = testclient.post(
        headers={"Host": "localhost.localdomain"},
        url="/persist",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
