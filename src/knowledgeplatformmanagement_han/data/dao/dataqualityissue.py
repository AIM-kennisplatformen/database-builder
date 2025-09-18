from typing import Any

from pydantic import BaseModel, RootModel


class Dataqualityissue(BaseModel, frozen=True):
    attributes: tuple[str]
    index_row: int
    input: Any
    message: str
    type: str


Dataqualityissues = RootModel[list[Dataqualityissue]]
