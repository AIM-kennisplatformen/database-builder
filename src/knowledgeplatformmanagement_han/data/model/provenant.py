from datetime import UTC, datetime
from enum import StrEnum, auto
from typing import Annotated

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlAttribute
from pydantic import ConfigDict, Field, FiniteFloat, PastDatetime, confloat


class Source(StrEnum):
    microsoft365 = auto()
    ubwfris = auto()
    documents = auto()


class Provenant[T](TypeqlAttribute[T]):
    model_config = ConfigDict(title="provenance")

    confidence: Annotated[FiniteFloat, confloat(gt=0.0, le=1.0)] = Field(title="confidence of veracity")
    """The confidence the attribute creator has in the veracity of this value."""
    datetime_end_recorded: PastDatetime | None = Field(default=None, title="timestamp of record")
    """A timestap of when the value was originally recorded in the data source."""
    datetime_end_updated: PastDatetime = Field(default=datetime.now(tz=UTC), title="timestamp of record update")
    """A timestap of when the value was recorded or changed in the target database."""
    source: Source = Field(title="source")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Provenant) and (self.confidence, self.source) == (other.confidence, other.source)


class ProvenantBoolean(Provenant[bool]):
    pass


class ProvenantDatetime(Provenant[datetime]):
    pass


class ProvenantDouble(Provenant[float]):
    pass


class ProvenantLong(Provenant[int]):
    pass


class ProvenantString(Provenant[str]):
    pass
