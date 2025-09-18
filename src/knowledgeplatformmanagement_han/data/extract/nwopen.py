from http.client import OK

import requests
from loguru import logger


# pylint: disable-next=too-few-public-methods
class Nwopen:
    def __init__(self) -> None:
        # TODO: Class isn't finished yet.
        raise NotImplementedError()

    def get_projects(self) -> None:
        # Define the API endpoint and parameters.
        url_api = (
            "https://nwopen-api.nwo.nl/NWOpen-API/api/Projects?organisation=%22Technische%20Universiteit%20Delft%22"
        )
        response = requests.get(url_api, timeout=120)
        if response.status_code == OK:
            data = response.json()
            for project in data["projects"]:
                logger.debug("Project ID: {}", project["project_id"])
                logger.debug("Title: {}", project["title"])
                logger.debug("Start Date: {}", project["start_date"])
                logger.debug("Summary (EN): {}\n", project.get("summary_en", "No summary available"))
                logger.debug(
                    "Members: \n{}",
                    "\n".join(
                        [
                            f"{member.get('role', 'No Role')}: {member.get('first_name', '(No First Name)')}"
                            f"{member.get('last_name', 'No Last Name')}"
                            for member in project["project_members"]
                        ],
                    ),
                )
        else:
            logger.error("Failed to retrieve data. Status code: {}.", response.status_code)
