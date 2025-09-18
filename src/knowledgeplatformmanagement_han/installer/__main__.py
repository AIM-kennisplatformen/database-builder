from anyio import run
from knowledgeplatformmanagement_generic.installer.__main__ import installer

from knowledgeplatformmanagement_han.settings import Configuration


async def main() -> None:
    configuration = Configuration()
    await installer(configuration=configuration)


if __name__ == "__main__":
    run(main)
