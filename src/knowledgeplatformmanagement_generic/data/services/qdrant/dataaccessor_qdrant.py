from contextvars import ContextVar
from types import TracebackType
from typing import Final

from docling.chunking import HybridChunker  # type: ignore[attr-defined]
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from knowledgeplatformmanagement_generic.data.services import Dataaccessor
from knowledgeplatformmanagement_generic.data.services.qdrant.connection_qdrant import ConnectionQdrant
from knowledgeplatformmanagement_generic.settings import Configuration

_asyncqdrantclient: ContextVar[AsyncQdrantClient] = ContextVar("asyncqdrantclient")


class DataaccessorQdrant(Dataaccessor[ConnectionQdrant]):
    def __init__(
        self,
        *,
        configuration: Configuration,
        model_encoder: SentenceTransformer,
    ) -> None:
        self.configuration: Final[Configuration] = configuration
        self._chunker = HybridChunker(
            max_tokens=model_encoder.get_max_seq_length(),
            merge_peers=True,
            tokenizer=self.configuration.name_model_encoder,
        )
        self._model_encoder = model_encoder
        self._length_chunk_max = self._model_encoder.get_max_seq_length()
        assert self._length_chunk_max

    async def __aenter__(self) -> ConnectionQdrant:
        # Duplication required due to Mypy defect.
        assert self._length_chunk_max
        _asyncqdrantclient.set(
            AsyncQdrantClient(
                cloud_inference=False,
                prefer_grpc=True,
                timeout=self.configuration.timeout_qdrant,
                url=str(self.configuration.url_qdrant),
            ),
        )
        return ConnectionQdrant(
            asyncqdrantclient=_asyncqdrantclient.get(),
            configuration=self.configuration,
            chunker=self._chunker,
            length_chunk_max=self._length_chunk_max,
            model_encoder=self._model_encoder,
        )

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        asyncqdrantclient = _asyncqdrantclient.get()
        await asyncqdrantclient.close()
        del asyncqdrantclient
