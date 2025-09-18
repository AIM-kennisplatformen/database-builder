from collections.abc import Generator
from itertools import chain

from knowledgeplatformmanagement_generic.data.services.typedb.typeql import TypeqlThing
from loguru import logger

from knowledgeplatformmanagement_han.data.dao.datasink import Datasink
from knowledgeplatformmanagement_han.data.model.document import Document
from knowledgeplatformmanagement_han.data.model.keyarea import Keyarea, Keyareas
from knowledgeplatformmanagement_han.data.model.projectlike import Projectlike
from knowledgeplatformmanagement_han.data.model.provenant import Source
from knowledgeplatformmanagement_han.data.model.researchuniversity import Researchuniversity
from knowledgeplatformmanagement_han.data.model.universityofappliedsciences import Universityofappliedsciences


# This implements a slim interface.
# pylint: disable-next=too-few-public-methods
class DatasinkDocuments(Datasink):
    def __init__(self) -> None:
        # TODO: Use a more principled way to insert these constant values. Adapt schema to have a single type per key
        # area with guaranteed exactly one instance.
        self.name_to_keyarea: dict[str, Keyarea] = {
            Keyareas.schoon.name: Keyarea(value=Keyareas.schoon, confidence=1.0, source=Source.documents),
            Keyareas.slim.name: Keyarea(value=Keyareas.slim, confidence=1.0, source=Source.documents),
            Keyareas.sociaal.name: Keyarea(value=Keyareas.sociaal, confidence=1.0, source=Source.documents),
        }
        self.hashvalue_to_document: dict[str, Document] = {}
        self.namelike_id_ubw_to_projectlike: dict[str, Projectlike] = {}
        self.namelike_name_to_researchuniversities: dict[str, Researchuniversity] = {}
        self.namelike_name_to_universityofappliedsciences: dict[str, Universityofappliedsciences] = {}

    def populate(self) -> Generator[TypeqlThing, None]:
        things = chain(
            self.name_to_keyarea.values(),
            self.hashvalue_to_document.values(),
            self.namelike_id_ubw_to_projectlike.values(),
            self.namelike_name_to_researchuniversities.values(),
            self.namelike_name_to_universityofappliedsciences.values(),
        )
        logger.info(
            "The documents datasink now contains (with count): {document} ({n_documents}), {researchuniversity} "
            "({n_researchuniversities}), {projectlike} ({n_projectlikes}) and {universityofappliedsciences} "
            "({n_universityofappliedsciencess}) ...",
            document=Document.model_config["title"],
            n_documents=len(self.hashvalue_to_document),
            n_projectlikes=len(self.namelike_id_ubw_to_projectlike),
            n_researchuniversities=len(self.namelike_name_to_researchuniversities),
            n_universityofappliedsciencess=len(self.namelike_name_to_universityofappliedsciences),
            projectlike=Projectlike.model_config["title"],
            researchuniversity=Researchuniversity.model_config["title"],
            universityofappliedsciences=Universityofappliedsciences.model_config["title"],
        )
        yield from things
