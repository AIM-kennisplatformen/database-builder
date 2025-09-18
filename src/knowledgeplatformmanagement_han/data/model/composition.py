from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingRelation
from pydantic import ConfigDict


class Composition(TypeqlThingRelation):
    model_config = ConfigDict(title="composition")
