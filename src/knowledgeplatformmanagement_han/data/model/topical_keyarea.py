from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.keyarea import Keyarea
from knowledgeplatformmanagement_han.data.model.topical import Topical


class TopicalKeyarea(Topical):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="topical")
    topic_keyarea: Key[Keyarea] = Field(title="topic")
