from pydantic import ConfigDict

from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike


# Wrapper type
# pylint: disable-next=too-few-public-methods
class Learningcommunity(Projectlike):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(title="learning community")
