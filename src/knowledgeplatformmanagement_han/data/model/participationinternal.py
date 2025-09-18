from knowledgeplatformmanagement_generic.data.services.typedb.typeql import Key, TypeqlThingRelation
from pydantic import ConfigDict, Field

from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike
from knowledgeplatformmanagement_han.data.model.school import School


class Participationinternal(TypeqlThingRelation):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="internal participation")

    internallycooperatingcomponents: Key[Projectlike] = Field(title="internally cooperating components")
    leadingcomponent: Key[School] = Field(title="leading HAN school")
    partnercomponent: Key[School] | None = Field(default=None, title="partner HAN school")
