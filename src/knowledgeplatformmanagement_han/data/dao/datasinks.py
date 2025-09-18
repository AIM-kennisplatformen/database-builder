from knowledgeplatformmanagement_han.data.dao.datasink_documents import DatasinkDocuments
from knowledgeplatformmanagement_han.data.dao.datasink_microsoft365 import DatasinkMicrosoft365
from knowledgeplatformmanagement_han.data.dao.datasink_ubwfris import DatasinkUbwfris


# This is a dataclass-like type, so custom public methods aren't expected.
# pylint: disable-next=too-few-public-methods
class Datasinks:
    documents: DatasinkDocuments
    microsoft365: DatasinkMicrosoft365
    ubwfris: DatasinkUbwfris

    def __init__(
        self,
        documents: DatasinkDocuments,
        microsoft365: DatasinkMicrosoft365,
        ubwfris: DatasinkUbwfris,
    ) -> None:
        self.documents = documents
        self.microsoft365 = microsoft365
        self.ubwfris = ubwfris
