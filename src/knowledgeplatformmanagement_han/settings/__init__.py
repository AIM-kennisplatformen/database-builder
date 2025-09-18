from typing import Annotated

from annotated_types import Ge
from knowledgeplatformmanagement_generic.settings import Configuration as ConfigurationGeneric
from pydantic import Field

from knowledgeplatformmanagement_han.settings.paths import Paths


class Configuration(ConfigurationGeneric):
    paths: Paths = Field(default_factory=Paths)
    size_max_workbook: Annotated[int, Ge(0)] = 16_777_216
