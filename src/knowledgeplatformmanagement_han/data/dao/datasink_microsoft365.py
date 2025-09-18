from collections.abc import Generator
from itertools import chain

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing
from loguru import logger

from knowledgeplatformmanagement_han.data.dao.datasink import Datasink
from knowledgeplatformmanagement_han.data.model.personmicrosoft365 import PersonMicrosoft365


# This implements a slim interface.
# pylint: disable-next=too-few-public-methods
class DatasinkMicrosoft365(Datasink):
    def __init__(self) -> None:
        self.address_email_to_personmicrosoft365: dict[str, PersonMicrosoft365] = {}

    def populate(self) -> Generator[TypeqlThing, None]:
        things = chain(self.address_email_to_personmicrosoft365.values())
        logger.info(
            "The Microsoft 365 datasink now contains (with count): {personmicrosoft365} ({n_personmicrosoft365}) ...",
            n_personmicrosoft365=len(self.address_email_to_personmicrosoft365),
            personmicrosoft365=PersonMicrosoft365.model_config["title"],
        )
        yield from things
