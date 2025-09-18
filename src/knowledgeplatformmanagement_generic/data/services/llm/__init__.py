from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from openai.types.chat.completion_create_params import ResponseFormat

from knowledgeplatformmanagement_generic.settings import Configuration


class OpenaiError(ValueError):
    def __init__(self) -> None:
        super().__init__("Failed to get LLM to respond.")


# This class does not require more public methods has a specific responsibility.
# pylint: disable-next=too-few-public-methods
class Llm:
    def __init__(self, *, configuration: Configuration, openai: OpenAI) -> None:
        """
        Wraps access to the LLM service.

        :param openai: The OpenAI-compatible LLM service.
        """
        self.configuration = configuration
        self.openai = openai

    async def prompt(self, *, content: str, responseformat: ResponseFormat) -> str:
        """
        Prompts the LLM service.

        :param content: The text of the prompt.
        :param responseformat: The format of the LLM response.
        :return: The LLM response content.
        """
        response = self.openai.chat.completions.create(
            messages=[
                ChatCompletionUserMessageParam(
                    role="user",
                    content=content,
                ),
            ],
            model=self.configuration.name_model_llm,
            response_format=responseformat,
        )
        if not response.choices[0].message.content:
            raise OpenaiError()
        return response.choices[0].message.content
