from collections.abc import AsyncGenerator, AsyncIterator, Callable


async def stream_json_list[T](
    iterator: AsyncIterator[T],
    itemrenderer: Callable[[T], str],
) -> AsyncGenerator[str, None]:
    first = True
    yield "["
    async for chunk in iterator:
        if not first:
            yield ","
        first = False
        yield itemrenderer(chunk)
    yield "]"
