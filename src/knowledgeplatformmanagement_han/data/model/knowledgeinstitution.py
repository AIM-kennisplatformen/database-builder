from pydantic import ConfigDict

from knowledgeplatformmanagement_han.data.model.institution import Institution


class Knowledgeinstitution(Institution):
    model_config = ConfigDict(title="knowledge institution")
