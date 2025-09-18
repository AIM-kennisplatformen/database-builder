from knowledgeplatformmanagement_han.data.model.educationalproject import Educationalproject
from knowledgeplatformmanagement_han.data.model.learningcommunity import Learningcommunity
from knowledgeplatformmanagement_han.data.model.operationalproject import Operationalproject
from knowledgeplatformmanagement_han.data.model.researchproject import Researchproject
from knowledgeplatformmanagement_han.data.model.strategicpartnership import Strategicpartnership
from knowledgeplatformmanagement_han.data.model.subproject import Subproject
from knowledgeplatformmanagement_han.data.model.unclearproject import Unclearproject

type Projectlikes = (
    Educationalproject
    | Learningcommunity
    | Operationalproject
    | Researchproject
    | Strategicpartnership
    | Unclearproject
    | Subproject
)
