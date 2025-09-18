from os import environ
from pathlib import Path
from typing import Any

from loguru import logger
from platformdirs import user_cache_dir, user_data_dir
from pydantic import BaseModel, Field

import knowledgeplatformmanagement_generic


# This is a dataclass and it has only two public attributes.
# pylint: disable-next=too-many-instance-attributes
class Paths(BaseModel):
    @staticmethod
    def get_dir_user_data(appname: str) -> Path:
        """
        Allow the user to use a ~/.local/share convention.
        """
        if str_path_dir_user_data := environ.get("XDG_DATA_HOME"):
            path_dir_user_data = Path(str_path_dir_user_data)
            logger.debug("You've set XDG_DATA_HOME to {}. Returning as user data directory.", path_dir_user_data)
            return Path(path_dir_user_data).expanduser().resolve(strict=True) / appname
        path_dir_user_data = Path(user_data_dir(appname=appname))
        logger.debug(
            "You haven't set XDG_DATA_HOME. Returning the OS default as the user data directory: '{!s}'.",
            path_dir_user_data,
        )
        return path_dir_user_data

    @staticmethod
    def get_dir_cache(appname: str) -> Path:
        """
        Allow the user to use a ~/.cache convention.
        """
        if str_path_dir_cache := environ.get("XDG_CACHE_HOME"):
            path_dir_cache = Path(str_path_dir_cache)
            logger.debug(
                "You've set the environment variable XDG_CACHE_HOME to '{!s}'. Returning as user cache directory.",
                path_dir_cache,
            )
            return Path(path_dir_cache).expanduser().resolve(strict=True) / appname
        path_dir_cache = Path(user_cache_dir(appname=appname))
        logger.debug(
            "You haven't set the environment variable XDG_CACHE_HOME. Returning the OS default as the user cache "
            "directory: '{!s}'.",
            path_dir_cache,
        )
        return path_dir_cache

    def _get_dir_artifacts(self) -> Path:
        return self.path_dir_user_data / "artifacts"

    def _get_dir_user_assets(self) -> Path:
        return self.path_dir_user_data / "assets"

    def _get_dir_root(self) -> Path:
        return Path(__file__).resolve(strict=True).parent.parent.parent.parent

    def _get_dir_test(self) -> Path:
        return self._path_dir_root / "tests"

    def _get_dir_logs(self) -> Path:
        return self.path_dir_user_cache / "logs"

    def _get_file_logs(self) -> Path:
        return self._path_dir_logs / "output.log"

    def _get_dir_model_spacy_en(self) -> Path:
        # Pylint does not understand Pydantic.
        # pylint: disable-next=no-member
        return self.path_dir_user_data.parent / "en_core_web_sm-3.8.0" / "en_core_web_sm" / "en_core_web_sm-3.8.0"

    def _get_dir_model_spacy_nl(self) -> Path:
        # Pylint does not understand Pydantic.
        # pylint: disable-next=no-member
        return self.path_dir_user_data.parent / "nl_core_news_lg-3.8.0" / "nl_core_news_lg" / "nl_core_news_lg-3.8.0"

    def _validate_dir_testdata(self) -> Path | None:
        if self.path_dir_testdata is not None:
            return self.path_dir_testdata.resolve(strict=True)
        return None

    _path_dir_artifacts: Path
    _path_dir_logs: Path
    _path_dir_root: Path
    _path_dir_root_test: Path
    _path_dir_user_assets: Path
    path_dir_user_cache: Path = Field(
        default=get_dir_cache(appname=knowledgeplatformmanagement_generic.__name__),
        frozen=True,
    )
    path_dir_user_data: Path = Field(
        default=get_dir_user_data(appname=knowledgeplatformmanagement_generic.__name__),
        frozen=True,
    )
    path_dir_testdata: Path | None = None
    _path_file_logs: Path
    _path_dir_model_spacy_en: Path
    _path_dir_model_spacy_nl: Path

    # The Ruff rule exceptions are needed to match Pydantic's intended design and use.
    def model_post_init(
        self,
        __context: Any,  # noqa: ANN401, PYI063
    ) -> None:
        self._path_dir_artifacts = self._get_dir_artifacts()
        self._path_dir_user_assets = self._get_dir_user_assets()
        self._path_dir_root = self._get_dir_root()
        self._path_dir_logs = self._get_dir_logs()
        self._path_dir_root_test = self._get_dir_test()
        self._path_file_logs = self._get_file_logs()
        self._path_dir_model_spacy_en = self._get_dir_model_spacy_en()
        self._path_dir_model_spacy_nl = self._get_dir_model_spacy_nl()
        self.path_dir_testdata = self._validate_dir_testdata()
