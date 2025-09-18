from io import BytesIO
from pathlib import Path
from tarfile import open as tarfile_open

from aiohttp import ClientSession
from anyio import run
from docling.utils.model_downloader import download_models
from easyocr import Reader
from huggingface_hub import snapshot_download
from loguru import logger
from spacy import load as spacy_load

from knowledgeplatformmanagement_generic.installer.exceptions import DirectoryHomeNotFoundError
from knowledgeplatformmanagement_generic.settings import Configuration


async def installer(configuration: Configuration) -> None:
    logger.debug("Configuration: {}.", configuration.model_dump_json(indent=2))
    logger.info(
        "Installing under user data directory '{!s}' and user cache directory '{!s}' ...",
        configuration.paths.path_dir_user_data,
        configuration.paths.path_dir_user_cache,
    )
    if not Path().home().exists():
        raise DirectoryHomeNotFoundError()
    configuration.paths.path_dir_user_data.mkdir(mode=0o700, parents=True)
    configuration.paths.path_dir_user_cache.mkdir(mode=0o700, parents=True)
    configuration.paths._path_dir_logs.mkdir(mode=0o700, parents=True)
    configuration.paths._path_dir_artifacts.mkdir(mode=0o700)
    configuration.paths._path_dir_user_assets.mkdir(mode=0o700)
    path_dir_model_docling = download_models(
        progress=True,
        with_code_formula=False,
        with_easyocr=False,
        with_picture_classifier=False,
        with_smolvlm=False,
    )
    logger.info("Downloaded Docling models to '{!s}'.", path_dir_model_docling)
    snapshot_download("bert-base-multilingual-cased", revision="main")
    snapshot_download("jinaai/jina-embeddings-v3", revision="main")
    snapshot_download("jinaai/xlm-roberta-flash-implementation", revision="main")
    # TODO: https://github.com/tomaarsen/SpanMarkerNER/issues/72
    snapshot_download("tomaarsen/span-marker-mbert-base-multinerd", revision="main")
    Reader(lang_list=["en", "nl"])
    for url_model_spacy in (
        f"https://github.com/explosion/spacy-models/releases/download/{model}"
        for model in (
            "en_core_web_sm-3.8.0/en_core_web_sm-3.8.0.tar.gz",
            "nl_core_news_lg-3.8.0/nl_core_news_lg-3.8.0.tar.gz",
        )
    ):
        async with (
            ClientSession() as session,
            session.get(url_model_spacy) as response,
        ):
            data = BytesIO(await response.read())
            with tarfile_open(fileobj=data, mode="r|gz") as tarfile:
                tarfile.extractall(configuration.paths._path_dir_model_spacy_nl.parent.parent.parent, filter="data")
    spacy_load(name=str(configuration.paths._path_dir_model_spacy_nl))
    spacy_load(name=str(configuration.paths._path_dir_model_spacy_en))
    logger.info("Installation succesful.")


async def main() -> None:
    configuration = Configuration()
    await installer(configuration=configuration)


if __name__ == "__main__":
    run(main)
