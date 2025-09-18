from typing import Annotated

from pydantic import StringConstraints

type NamelikeIdEmployee = Annotated[str, StringConstraints(pattern=r"^(\d+|999-.+ .+|[A-Z]+)$")]
