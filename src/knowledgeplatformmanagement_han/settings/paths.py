from pathlib import Path

from knowledgeplatformmanagement_generic.settings.paths import Paths as PathsGeneric

import knowledgeplatformmanagement_han


# This is a dataclass and it has only two public attributes.
# pylint: disable-next=too-many-instance-attributes
class Paths(PathsGeneric):
    path_dir_user_cache: Path = PathsGeneric.get_dir_cache(appname=knowledgeplatformmanagement_han.__name__)
    path_dir_user_data: Path = PathsGeneric.get_dir_user_data(appname=knowledgeplatformmanagement_han.__name__)
