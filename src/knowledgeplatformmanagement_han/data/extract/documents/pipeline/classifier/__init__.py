from string import Template
from typing import Annotated, TypedDict

from anyio import Path
from knowledgeplatformmanagement_generic.data.services.llm.dataaccessor_llm import DataaccessorLlm
from loguru import logger
from openai.types.shared_params.response_format_json_object import ResponseFormatJSONObject
from pandas import DataFrame
from pydantic import BaseModel, StringConstraints

from knowledgeplatformmanagement_han.data.extract.documents.proposal import Proposal
from knowledgeplatformmanagement_han.settings import Configuration


class Keyareas(TypedDict):
    schoon: bool
    slim: bool
    sociaal: bool


class ClassifyKeyareas(BaseModel, frozen=True):
    keyarea: Keyareas
    rationale: Annotated[str, StringConstraints(min_length=5)]


class ClassifierOpenaiError(ValueError):
    def __init__(self) -> None:
        super().__init__("Failed to get OpenAI to respond with classification.")


# This class does not require more public methods has a specific responsibility.
# pylint: disable-next=too-few-public-methods
class ProposalKeyareaClassifier:
    def __init__(self, *, configuration: Configuration, dataaccessor_llm: DataaccessorLlm) -> None:
        """
        Initializes the classifier with the necessary configurations.

        Args:
            configuration: Global configuration.
            dataaccessor_llm: LLM service.
        """
        self.configuration = configuration
        self.dataaccessor_llm = dataaccessor_llm
        self.sections: dict[str, list[str | DataFrame]]

    async def _classify(self, *, text: str) -> str:
        """
        Classifies a text into one or more HAN Key Areas.

        :param text: The text of the document to classify.
        :return: A dictionary containing the classification and rationale.
        """
        async with await (
            await (Path(__file__) / ".." / "queries" / "openai" / "ProposalKeyareaClassifier-1.md").resolve(strict=True)
        ).open(encoding="utf-8") as file_prompt:
            template = Template(await file_prompt.read())
        prompt = template.substitute(proposal=text)
        async with self.dataaccessor_llm as _connectionllm:
            return await _connectionllm._llm.prompt(
                content=prompt,
                responseformat=ResponseFormatJSONObject(type="json_object"),
            )

    async def run_pipeline(self, proposal: Proposal) -> ClassifyKeyareas:
        """
        Executes the complete pipeline of loading, extracting, filtering, and classifying.
        """
        logger.debug("Classifying Proposal ...")
        classification = await self._classify(text=proposal.summary)
        return ClassifyKeyareas.model_validate_json(json_data=classification)
