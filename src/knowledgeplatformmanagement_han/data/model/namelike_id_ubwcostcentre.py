from typing import Annotated

from pydantic import StringConstraints

type NamelikeIdUbwcostcentre = Annotated[str, StringConstraints(pattern=r"^\d+$")]
