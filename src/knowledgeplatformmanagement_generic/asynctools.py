from collections.abc import AsyncIterator, Iterator
from queue import Queue

import anyio
from anyio import from_thread, run, to_thread
from anyio.lowlevel import checkpoint


def async_generator_to_regular[T](asyncgenerator: AsyncIterator[T]) -> Iterator[T]:
    """
    Lazily converts an async generator into a synchronous iterator.
    Uses a blocking queue (with a background pump scheduled via an AnyIO task group)
    to yield items as they become available.
    """
    queue: Queue[T] = Queue()
    # Unique marker to signal end of iteration.
    sentinel = object()

    async def pump() -> None:
        # It’s not possible syntactically to make the scope of the `try` block smaller.
        # pylint: disable-next=too-many-try-statements
        try:
            async for item in asyncgenerator:
                queue.put(item)
        finally:
            # TODO: Fix Mypy when under Python >3.12, using `queue.shutdown()`.
            queue.put(sentinel)  # type: ignore[arg-type]

    async def schedule_pump() -> None:
        # Create a task group and use `start_soon()` to schedule pump.
        # Note: the async context will not exit until pump completes.
        async with anyio.create_task_group() as taskgroup:
            taskgroup.start_soon(pump)
            await checkpoint()

    with from_thread.start_blocking_portal() as portal:
        portal.start_task_soon(to_thread.run_sync, lambda: run(schedule_pump))
        # The portal returns immediately after scheduling the background task.

    # Synchronous generator: block on `queue.get()` until sentinel is received.
    # pylint: disable-next=while-used
    while (item := queue.get()) is not sentinel:
        yield item
