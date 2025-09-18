from pydantic import ConfigDict

from knowledgeplatformmanagement_han.data.model.document import Document


class Proposal(Document):
    def nonabstract_marker(self) -> None:
        pass

    model_config = ConfigDict(frozen=True, title="research proposal")
