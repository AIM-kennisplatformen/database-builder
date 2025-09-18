from typing import Annotated

from annotated_types import Ge, Le
from pydantic import AnyHttpUrl, BaseModel, Field, IPvAnyInterface, StringConstraints
from typedb.driver import TypeDB

from knowledgeplatformmanagement_generic.settings.paths import Paths


class Configuration(BaseModel, frozen=True):
    address_typedb: IPvAnyInterface = TypeDB.DEFAULT_ADDRESS.split(sep=":", maxsplit=1)[0]
    fastapi_debug: bool = True
    """The address TypeDB Core listens on."""
    port_typedb: Annotated[int, Ge(0), Le(65535)] = int(TypeDB.DEFAULT_ADDRESS.split(sep=":", maxsplit=1)[1])
    """The TCP port TypeDB Core listens on."""
    name_database: Annotated[str, StringConstraints(min_length=1)] = Field(default="knowledgeplatform")
    """The name of the TypeDB and Qdrant databases."""
    name_model_encoder: Annotated[str, StringConstraints(min_length=1)] = "jinaai/jina-embeddings-v3"
    name_model_llm: Annotated[str, StringConstraints(min_length=1)] = "gpt-4o-mini"
    """The name of the LLM model to use with the LLM service."""
    paths: Paths = Field(default_factory=Paths)
    port: Annotated[int, Ge(0), Le(65535)] = 8080
    """The TCP port the webserver listens on."""
    size_max_workbook: Annotated[int, Ge(0)] = 16_777_216
    size_max_document: Annotated[int, Ge(0)] = 67_108_864
    timeout_perdocument: Annotated[int, Ge(1)] = 180
    """The maximum number of seconds to take to index a single document."""
    timeout_qdrant: Annotated[int, Ge(1)] = 60
    url_qdrant: AnyHttpUrl = AnyHttpUrl("http://localhost:6334")
    """The connection string (URL) to the Qdrant server."""
    qdrant_size_batch: Annotated[int, Ge(1)] = 1024
