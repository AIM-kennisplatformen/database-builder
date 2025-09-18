from collections.abc import AsyncIterator, Iterable

from pydantic import BaseModel
from pytest import mark

from knowledgeplatformmanagement_generic.web import stream_json_list


class Test(BaseModel):
    name: str
    number: int


async def yielder[T](*, items: Iterable[T]) -> AsyncIterator[T]:
    for item in items:
        yield item


@mark.anyio(scope="module")
async def test_stream_json_list() -> None:
    list1 = [Test(name="", number=1), Test(name="hello", number=2), Test(name=".\\", number=3)]
    assert (
        "".join(
            [item async for item in stream_json_list(iterator=yielder(items=list1), itemrenderer=Test.model_dump_json)],
        )
        == r'[{"name":"","number":1},{"name":"hello","number":2},{"name":".\\","number":3}]'
    )
