from typing import Annotated

from pydantic import StringConstraints

type NamelikeIdSchool = Annotated[str, StringConstraints(pattern=r"^\d+$")]
