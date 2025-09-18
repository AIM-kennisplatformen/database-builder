"""A pipeline for converting and processing documents using Docling.

The PipelineDocuments class provides functionality to convert various document formats to Docling documents and handle
document processing workflows.
"""

from collections.abc import Iterable, Iterator, Sequence
from io import BytesIO
from os import PathLike
from pathlib import Path as PathSync
from pprint import pformat
from typing import IO

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import (  # type: ignore[attr-defined]
    ConversionResult,
    ConversionStatus,
    DocumentStream,
    ErrorItem,
)
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions, PipelineOptions
from docling.datamodel.settings import settings
from docling.document_converter import (
    CsvFormatOption,
    DocumentConverter,
    ExcelFormatOption,
    HTMLFormatOption,
    MarkdownFormatOption,
    PdfFormatOption,
    PowerpointFormatOption,
    WordFormatOption,
)

# TODO: See https://github.com/DS4SD/docling/issues/614
from docling_core.types.doc import DoclingDocument  # type: ignore[attr-defined]
from loguru import logger
from pydantic.dataclasses import dataclass

from knowledgeplatformmanagement_generic.settings import Configuration


@dataclass(frozen=True, kw_only=True)
class Faultss:
    faults: Sequence[ErrorItem]
    hashvalue: str
    path_file_document: PathLike[str]


class PipelineDocumentsConversionUnsupportedError(ValueError):
    def __init__(self, *, extension: str) -> None:
        super().__init__(f"Raw document type not supported, based on its filename extension {extension}.")


class PipelineDocumentsConversionFailedError(ValueError):
    def __init__(self, *, faultss: Sequence[Faultss]) -> None:
        self.faultss = faultss
        for faults in self.faultss:
            super().__init__(
                f"Failed to convert raw document '{faults.path_file_document!s}' ({faults.hashvalue}) "
                f"because of {len(faults.faults)} fault(s): {pformat(faults.faults)}",
            )


class PipelineDocuments:
    def __init__(
        self,
        *,
        configuration: Configuration,
        path_dir_artifacts: str | None = None,
    ) -> None:
        """Initialize the raw document to Docling document conversion pipeline.

        Configures a document converter with support for multiple file formats and processing settings. Sets up CSV,
        PDF, Microsoft Word, HTML, Markdown, Microsoft PowerPoint, and Microsoft Excel document conversion.

        Args:
            configuration: Global configuration.
            path_dir_artifacts: Optional path from which to source predictive models.
        """
        self.configuration = configuration
        pdfpipelineoptions = PdfPipelineOptions(
            artifacts_path=path_dir_artifacts,
            do_ocr=False,
            document_timeout=self.configuration.timeout_perdocument,
            ocr_options=EasyOcrOptions(download_enabled=False, lang=["en", "nl"]),
        )
        pipelineoptions = PipelineOptions(document_timeout=self.configuration.timeout_perdocument)
        settings.debug.debug_output_path = str(self.configuration.paths._path_dir_logs)
        self.documentconverter = DocumentConverter(
            allowed_formats=[
                InputFormat.CSV,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.MD,
                InputFormat.PDF,
                InputFormat.PPTX,
                InputFormat.XLSX,
            ],
            format_options={
                InputFormat.CSV: CsvFormatOption(pipeline_options=pipelineoptions),
                InputFormat.DOCX: WordFormatOption(pipeline_options=pipelineoptions),
                InputFormat.HTML: HTMLFormatOption(pipeline_options=pipelineoptions),
                InputFormat.MD: MarkdownFormatOption(pipeline_options=pipelineoptions),
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pdfpipelineoptions,
                    backend=PyPdfiumDocumentBackend,
                ),
                InputFormat.PPTX: PowerpointFormatOption(pipeline_options=pipelineoptions),
                InputFormat.XLSX: ExcelFormatOption(pipeline_options=pipelineoptions),
            },
        )

    def _process_conversionresults(
        self,
        *,
        conversionresults: Iterable[ConversionResult],
    ) -> Iterator[DoclingDocument | PipelineDocumentsConversionFailedError]:
        faultss = []
        for conversionresult in conversionresults:
            for fault in conversionresult.errors:
                logger.error(
                    "Fault when converting document '{path!s}' (hash value: {hashvalue}): {fault}.",
                    fault=fault,
                    hashvalue=conversionresult.input.document_hash,
                    path=conversionresult.input.file,
                )
            if conversionresult.errors:
                faultss.append(
                    Faultss(
                        path_file_document=conversionresult.input.file,
                        hashvalue=conversionresult.input.document_hash,
                        faults=conversionresult.errors,
                    ),
                )
            if conversionresult.status == ConversionStatus.SUCCESS:
                logger.info(
                    "Converted document '{path!s}' (hash value: {hashvalue}, integer hash value: {hashvalue_integer}).",
                    hashvalue_integer=(
                        conversionresult.document.origin.binary_hash if conversionresult.document.origin else 0
                    ),
                    hashvalue=conversionresult.input.document_hash,
                    path=conversionresult.input.file,
                )
                yield conversionresult.document
            else:
                logger.error(
                    "Converting document '{path!s}' (hash value: {hashvalue}) didn't succeed (fully, yet).",
                    hashvalue=conversionresult.input.document_hash,
                    path=conversionresult.input.file,
                )
        if faultss:
            yield PipelineDocumentsConversionFailedError(faultss=faultss)

    def produce_doclingdocuments(
        self,
        *,
        sources: Iterable[PathSync | DocumentStream],
    ) -> Iterator[DoclingDocument | PipelineDocumentsConversionFailedError]:
        """Convert a sequence of raw documents (sources) to `DoclingDocument`s.

        Its raw document converter supports a number formats, as supported by Docling, and suppresses conversion errors.

        Args:
            `sources`: The file paths or `DocumentStream`s to be converted.

        Yields:
            Converted documents from the input file paths or` PipelineDocumentsConversionFailedError`s.
        """
        conversionresults: Iterator[ConversionResult] = self.documentconverter.convert_all(
            raises_on_error=False,
            source=sources,
        )
        yield from self._process_conversionresults(conversionresults=conversionresults)

    def produce_doclingdocument(
        self,
        *,
        name_document: str,
        data_document: IO[bytes],
    ) -> DoclingDocument | PipelineDocumentsConversionFailedError:
        """Convert a sequence of raw document files to Docling documents using a document converter.

        Its raw document converter supports a number formats, as supported by Docling, and suppresses conversion errors.

        Args:
            name_document: a name for the document, for use by Docling.
            data_document: the document.

        Returns:
            DoclingDocument | PipelineDocumentsConversionFailedError: Converted document or an exception.
        """
        # TODO: Upstream Docling: must it be BytesIO?
        conversionresult = self.documentconverter.convert(
            max_file_size=self.configuration.size_max_document,
            source=DocumentStream(name=name_document, stream=BytesIO(data_document.read())),
            raises_on_error=False,
        )
        return next(
            self._process_conversionresults(
                conversionresults=(conversionresult,),
            ),
        )
