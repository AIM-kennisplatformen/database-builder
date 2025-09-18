from collections.abc import Iterable
from hashlib import blake2b
from typing import Any, Final, TypedDict

# TODO: See https://github.com/DS4SD/docling/issues/614
from docling.chunking import BaseChunker  # type: ignore[attr-defined]
from docling.datamodel.document import DoclingDocument  # type: ignore[attr-defined]
from docling_core.types.doc import DocumentOrigin  # type: ignore[attr-defined]
from docling_core.types.doc.document import Uint64
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions.common_types import ScoredPoint, StrictModeConfig, VectorParams
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    IsEmptyCondition,
    MatchValue,
    OptimizersConfigDiff,
    PayloadField,
    PointStruct,
)
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from knowledgeplatformmanagement_generic.data.extract.documents.document import Document
from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing
from knowledgeplatformmanagement_generic.settings import Configuration


class PayloadChunk(TypedDict):
    hashvalue: str
    text: str


class PayloadFulldocument(TypedDict):
    doclingdocument: dict[str, Any]
    hashvalue: str
    name_file: str
    language: str
    mediatype: str
    sectiontitles: list[str]
    text_full: str
    text_summary: str


class ConnectionQdrantDocumentstoreError(ValueError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Failed to store document '{name}', since it misses an `origin` attribute.")


# We use this abstraction as part of architectural design, even if right now there are few public methods.
# TODO: Add methods.
# pylint: disable-next=too-few-public-methods
class ConnectionQdrant:
    def __init__(
        self,
        *,
        asyncqdrantclient: AsyncQdrantClient,
        chunker: BaseChunker,
        configuration: Configuration,
        length_chunk_max: int,
        model_encoder: SentenceTransformer,
    ) -> None:
        self._asyncqdrantclient: Final[AsyncQdrantClient] = asyncqdrantclient
        self._chunker: Final[BaseChunker] = chunker
        self._length_chunk_max: Final[int] = length_chunk_max
        self._model_encoder: Final[SentenceTransformer] = model_encoder
        self.configuration: Final[Configuration] = configuration

    async def create_collection(self) -> bool:
        logger.info(
            "Creating Qdrant collection ({name_database}) ...",
            name_database=self.configuration.name_database,
        )
        return await self._asyncqdrantclient.create_collection(
            collection_name=self.configuration.name_database,
            # TODO: Update indexing threshold after persisting. Configure indexing properly in the first place
            # https://qdrant.tech/documentation/concepts/indexing/
            optimizers_config=OptimizersConfigDiff(indexing_threshold=0, default_segment_number=2),
            shard_number=4,
            strict_mode_config=StrictModeConfig(enabled=True),
            vectors_config=VectorParams(
                distance=Distance.COSINE,
                on_disk=True,
                size=self._model_encoder.get_sentence_embedding_dimension(),
            ),
        )

    async def check_document_already_inserted(self, *, hashvalue: str) -> bool:
        """Check whether a document with a certain integer hash value (as produced by Docling) was already inserted.
        The result is based on whether at least one Point with the hash value is already stored in Qdrant.

        Args:
            hashvalue: integer hash value (as produced by Docling). Must be a string to avoid integer overflow.
        """
        filter_alreadyindexed = Filter(
            must=[FieldCondition(key="hashvalue", match=MatchValue(value=hashvalue))],
        )
        points, _ = await self._asyncqdrantclient.scroll(
            collection_name=self.configuration.name_database,
            limit=1,
            scroll_filter=filter_alreadyindexed,
            with_payload=False,
            with_vectors=False,
        )
        return bool(points and points[0] and points[0].payload)

    async def insert_typeqlthings(
        self,
        *,
        typeqlthings: Iterable[TypeqlThing],
    ) -> None:
        logger.trace(
            "Inserting TypeQL things into Qdrant collection ({name_database}) ...",
            name_database=self.configuration.name_database,
        )
        self._asyncqdrantclient.upload_points(
            batch_size=self.configuration.qdrant_size_batch,
            collection_name=self.configuration.name_database,
            points=(
                PointStruct(
                    # Must be reduced to six bits because of https://github.com/qdrant/qdrant-client/issues/936/.
                    id=int.from_bytes(
                        blake2b(str_typeqlthing.encode(), digest_size=6).digest(),
                        byteorder="little",
                        signed=False,
                    )
                    & ((1 << 53) - 1),
                    payload={"text": str_typeqlthing},
                    vector=self._model_encoder.encode(
                        str_typeqlthing,
                        task="retrieval.passage",
                    ).tolist(),
                )
                for typeqlthing in tqdm(typeqlthings)
                if (str_typeqlthing := str(typeqlthing))
            ),
        )

    async def insert_document(
        self,
        *,
        doclingdocument: DoclingDocument,
    ) -> Uint64:
        """Store Docling document and its chunks.

        Does not overwrite stored documents with the same integer hash value, which can be relevant if the stored
        contents differ because of, e.g., Docling version differences.

        Returns: integer hash value of the document file.
        """
        if not doclingdocument.origin:
            raise ConnectionQdrantDocumentstoreError(name=doclingdocument.name)
        hashvalue_integer = doclingdocument.origin.binary_hash
        logger.trace(
            "Inserting document '{name_file}' (integer hash value: {hashvalue_integer}) and its chunks into Qdrant "
            "collection ({name_database}) ...",
            hashvalue_integer=hashvalue_integer,
            name_file=doclingdocument.origin.filename,
            name_database=self.configuration.name_database,
        )
        if await self.check_document_already_inserted(hashvalue=str(doclingdocument.origin.binary_hash)):
            logger.debug(
                "Skipping document (name: '{name_file}', integer hash value: {hashvalue_integer}), as it's already "
                "stored in the Qdrant collection.",
                hashvalue_integer=hashvalue_integer,
                name_file=doclingdocument.origin.filename,
            )
        else:
            logger.debug(
                "Vectorizing document (name: '{name_file}', integer hash value: {hashvalue_integer}) ...",
                hashvalue_integer=hashvalue_integer,
                name_file=doclingdocument.origin.filename,
            )
            document = Document(configuration=self.configuration, doclingdocument=doclingdocument)
            document.summarize()
            # TODO: Serialize our own Document-objects rather than DoclingDocuments.
            # TODO: Store documents in TypeDB database instead of on-disk?
            doclingdocument_origin_dump = doclingdocument.origin.model_dump(
                include={"binary_hash", "mimetype", "filename"},
            )
            # Prepare document chunks.
            hashvalue_str = str(doclingdocument_origin_dump["binary_hash"])
            payload_chunks = PayloadChunk(
                # This integer can be too large to fit in the integer datatype that Qdrant converts it to, so
                # convert to string. See also https://github.com/qdrant/qdrant-client/issues/936.
                hashvalue=hashvalue_str,
                text="",
            )
            pointstructs = [
                PointStruct(
                    id=int.from_bytes(
                        blake2b(text.encode(), digest_size=6).digest(),
                        byteorder="little",
                        signed=False,
                    )
                    & ((1 << 53) - 1),
                    payload=payload_chunks | {"text": text},
                    vector=self._model_encoder.encode(
                        # TODO: Fix overlong chunk handling.
                        text,
                        task="retrieval.passage",
                    ).tolist(),
                )
                for chunk in self._chunker.chunk(dl_doc=doclingdocument)
                if (text := self._chunker.serialize(chunk)[: self._length_chunk_max])
            ]
            # Overwrite because this information is duplicated in the payload, and because it can contain a large
            # integers that Qdrant can't handle.
            doclingdocument.origin = None
            # Prepare full document.
            payload_fulldocument = PayloadFulldocument(
                doclingdocument=doclingdocument.export_to_dict(),
                hashvalue=hashvalue_str,
                language=document.language.name,
                mediatype=doclingdocument_origin_dump["mimetype"],
                name_file=doclingdocument_origin_dump["filename"],
                sectiontitles=list(document.sectiontitle_to_flatsection.keys()),
                text_full=document.text_full,
                text_summary=document.summary,
            )
            pointstructs.append(
                PointStruct(
                    id=int.from_bytes(
                        blake2b(hashvalue_str.encode(), digest_size=6).digest(),
                        byteorder="little",
                        signed=False,
                    )
                    & ((1 << 53) - 1),
                    payload=payload_fulldocument,
                    vector={},
                ),
            )
            self._asyncqdrantclient.upload_points(
                collection_name=self.configuration.name_database,
                points=pointstructs,
            )
            logger.info(
                "Stored document '{name_file}' (integer hash value: {hashvalue_integer}) and its chunks in Qdrant.",
                hashvalue_integer=hashvalue_integer,
                name_file=doclingdocument_origin_dump["filename"],
            )
        return hashvalue_integer

    async def fetch_full_document(self, *, hashvalue_document: Uint64) -> DoclingDocument | None:
        """
        Load a Docling document or convert a raw document file (insofar supported by Docling) to a Docling document.
        """
        logger.debug("Fetching full document (integer hash value: {}) ...", hashvalue_document)
        filter_fulldocument = Filter(
            must=[FieldCondition(key="hashvalue", match=MatchValue(value=str(hashvalue_document)))],
            must_not=[IsEmptyCondition(is_empty=PayloadField(key="text_full"))],
        )
        points, offset = await self._asyncqdrantclient.scroll(
            collection_name=self.configuration.name_database,
            limit=1,
            scroll_filter=filter_fulldocument,
            with_payload=True,
            with_vectors=True,
        )
        assert offset is None
        if points and points[0] and points[0].payload and (doclingdocument_str := points[0].payload["doclingdocument"]):
            doclingdocument = DoclingDocument.model_validate(doclingdocument_str)
            assert not doclingdocument.origin
            doclingdocument.origin = DocumentOrigin(
                mimetype=points[0].payload["mediatype"],
                binary_hash=int(points[0].payload["hashvalue"]),
                filename=points[0].payload["name_file"],
            )
            return doclingdocument
        return None

    async def fetch_query_vectors(
        self,
        *,
        limit: int,
        query: str,
    ) -> list[ScoredPoint]:
        logger.debug("Fetching retrieval vectors for query ...")
        queryvector = self._model_encoder.encode(
            query,
            prompt="retrieval.query",
            task="retrieval.query",
        ).tolist()
        filter_knowledgeplatform = Filter(
            should=[
                IsEmptyCondition(is_empty=PayloadField(key="text")),
                IsEmptyCondition(is_empty=PayloadField(key="text_full")),
            ],
            must_not=[
                IsEmptyCondition(is_empty=PayloadField(key="hashvalue")),
            ],
        )
        return await self._asyncqdrantclient.search(
            collection_name=self.configuration.name_database,
            limit=limit,
            query_filter=filter_knowledgeplatform,
            query_vector=queryvector,
        )
