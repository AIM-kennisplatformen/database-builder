from anyio import Path
from docling_core.types.doc.document import Uint64
from fastapi import status
from fastapi.testclient import TestClient
from pytest import mark

from knowledgeplatformmanagement_han.data.extract.documents.pipeline.classifier import ClassifyKeyareas

from .test_common import _persist

HASHVALUE_BINARY_FILE_PROJECTPROPOSALTEST = 1230198746648155557


async def _classify_keyareas(
    *,
    hashvalue_proposal: Uint64,
    testclient: TestClient,
) -> ClassifyKeyareas:
    response = testclient.put(
        headers={"Host": "localhost.localdomain"},
        url=f"/documents/classify/keyareas/{hashvalue_proposal}",
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    return ClassifyKeyareas.model_validate_json(json_data=response.text)


async def _document_insert(
    *,
    testclient: TestClient,
) -> Uint64:
    path_file_document = await (
        Path(__file__).parent.parent / "data" / "extract" / "documents" / "ProjectProposalTest.pdf"
    ).resolve(
        strict=True,
    )
    response = testclient.post(
        headers={
            "Content-Disposition": f'attachment; filename="{path_file_document.name}"',
            "Host": "localhost.localdomain",
        },
        url="/documents/insert",
        content=await path_file_document.read_bytes(),
    )
    assert response.status_code == status.HTTP_200_OK and response.headers["Content-Type"] == "application/json"
    return Uint64(response.json()["hashvalue"])


async def _extract_partners(
    *,
    hashvalue_proposal: Uint64,
    testclient: TestClient,
) -> None:
    response = testclient.put(
        headers={"Host": "localhost.localdomain"},
        url=f"/documents/extract/partners/{hashvalue_proposal}",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@mark.slow(reason="Calls a remote LLM service.")
@mark.anyio(scope="module")
async def test_classifiy_keyareas(
    *,
    testclient: TestClient,
) -> None:
    hashvalue_binary = await _document_insert(testclient=testclient)
    assert hashvalue_binary == HASHVALUE_BINARY_FILE_PROJECTPROPOSALTEST
    classifykeyareas = await _classify_keyareas(hashvalue_proposal=hashvalue_binary, testclient=testclient)
    # The actual prediction can't be part of the assertion, since the prediction isn’t stable.
    assert all(keyarea in classifykeyareas.keyarea for keyarea in ("schoon", "slim", "sociaal"))


@mark.anyio(scope="module")
async def test_extract_partners(
    *,
    testclient: TestClient,
) -> None:
    hashvalue_binary = await _document_insert(testclient=testclient)
    assert hashvalue_binary == HASHVALUE_BINARY_FILE_PROJECTPROPOSALTEST
    await _extract_partners(hashvalue_proposal=hashvalue_binary, testclient=testclient)
    await _persist(testclient=testclient)
