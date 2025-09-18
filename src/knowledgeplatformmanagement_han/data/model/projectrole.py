from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThingRelation
from pydantic import ConfigDict


class Projectrole(TypeqlThingRelation):
    model_config = ConfigDict(title="project role")
