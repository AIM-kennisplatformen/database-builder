from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key, TypeqlThingRelation
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike
from knowledgeplatformmanagement_han.data.model.topic import Topic


class Topical(TypeqlThingRelation):
    model_config = ConfigDict(title="topical")
    agent: Key[Projectlike] = Field(title="agent")
    topic: Key[Topic] = Field(title="topic")
