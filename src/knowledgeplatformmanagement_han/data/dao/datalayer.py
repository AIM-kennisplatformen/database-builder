from collections.abc import AsyncGenerator
from datetime import datetime
from importlib.resources import as_file, files
from typing import Any, ClassVar, cast

from anyio import Path
from knowledgeplatformmanagement_generic.data.services.llm.dataaccessor_llm import DataaccessorLlm
from knowledgeplatformmanagement_generic.data.services.qdrant.dataaccessor_qdrant import DataaccessorQdrant
from knowledgeplatformmanagement_generic.data.services.typedb.dataaccessor_typedb import DataaccessorTypedb
from loguru import logger
from sentence_transformers import SentenceTransformer

import knowledgeplatformmanagement_han
from knowledgeplatformmanagement_han.data.dao.datasinks import Datasinks
from knowledgeplatformmanagement_han.data.extract.ubwfris import ExportPowerbiPerson, ExportPowerbiTimesheet
from knowledgeplatformmanagement_han.settings import Configuration
from knowledgeplatformmanagement_han.settings.timesheets import ProjecttypeToProjecttypeinfo, Projecttypeinfo


class Datalayer:
    # TODO: Move to front-end.
    PROJECTCLASSIFIER_FINANCIAL_TO_PROJECTTYPE: ClassVar[dict[str, str]] = {
        enumvalue.value.projectclassifier_financial: enumname
        for enumname, enumvalue in ProjecttypeToProjecttypeinfo.__members__.items()
        if enumvalue.value.projectclassifier_financial
    }

    # The multitude of arguments is required for this data-carrying class.
    def __init__(  # noqa: PLR0913
        self,
        *,
        configuration: Configuration,
        dataaccessor_llm: DataaccessorLlm,
        dataaccessor_typedb: DataaccessorTypedb,
        dataaccessor_qdrant: DataaccessorQdrant,
        datasinks: Datasinks,
        model_encoder: SentenceTransformer,
    ) -> None:
        self.configuration = configuration
        self.dataaccessor_llm = dataaccessor_llm
        self.dataaccessor_typedb = dataaccessor_typedb
        self.dataaccessor_qdrant = dataaccessor_qdrant
        self.datasinks = datasinks
        self.model_encoder = model_encoder

    async def init(self) -> None:
        """Creates all data stores configured in this data layer. Assumes a clean slate."""
        async with self.dataaccessor_typedb as connection_typedb:
            connection_typedb.create_database()
            logger.info(
                "Created TypeDB database ({name_database}).",
                name_database=self.configuration.name_database,
            )
            with as_file(files(knowledgeplatformmanagement_han).joinpath("schema.tql")) as path_file_query_schema:
                await connection_typedb.create_schema(
                    path_file_schema=Path(path_file_query_schema),
                )
            logger.info(
                "Wrote the schema to the TypeDB database ({name_database}).",
                name_database=self.configuration.name_database,
            )
        async with self.dataaccessor_qdrant as connection_qdrant:
            await connection_qdrant.create_collection()

    async def persist(self) -> None:
        async with self.dataaccessor_qdrant as connection_qdrant:
            # TODO: Lock storage for writes after insertions, in production.
            await connection_qdrant.insert_typeqlthings(typeqlthings=self.datasinks.documents.populate())
            await connection_qdrant.insert_typeqlthings(typeqlthings=self.datasinks.microsoft365.populate())
            await connection_qdrant.insert_typeqlthings(
                typeqlthings=self.datasinks.ubwfris.populate(),
            )
        async with self.dataaccessor_typedb as connection_typedb:
            await connection_typedb.insert_typeqlthings(typeqlthings=self.datasinks.documents.populate())
            await connection_typedb.insert_typeqlthings(typeqlthings=self.datasinks.microsoft365.populate())
            await connection_typedb.insert_typeqlthings(typeqlthings=self.datasinks.ubwfris.populate())

    async def clear(self) -> None:
        """Clears all data stores configured in this data layer. Destructive!"""
        async with self.dataaccessor_typedb as connection_typedb:
            connection_typedb.delete_database()
            logger.info(
                "Deleted TypeDB database ({name_database}).",
                name_database=self.configuration.name_database,
            )
        async with self.dataaccessor_qdrant as connection_qdrant:
            await connection_qdrant._asyncqdrantclient.delete_collection(
                collection_name=self.configuration.name_database,
            )
            logger.info(
                "Deleted Qdrant collection ({name_database}).",
                name_database=self.configuration.name_database,
            )

    # TODO: Move to front-end.
    def _export_powerbi_timesheet(self, hoursallocation: dict[str, Any]) -> ExportPowerbiTimesheet:
        namelike_id_ubw = cast(str, hoursallocation["subproject"]["namelike_id_ubw"][0]["value"])
        projectclassifier_financial = cast(
            str,
            hoursallocation["subproject"]["projectclassifier_financial"][0]["value"],
        )
        projecttype = self.PROJECTCLASSIFIER_FINANCIAL_TO_PROJECTTYPE[projectclassifier_financial]
        projecttypeinfo: Projecttypeinfo = ProjecttypeToProjecttypeinfo[projecttype].value
        return ExportPowerbiTimesheet(
            billable=cast(bool, hoursallocation["timesheet"]["billable"][0]["value"]),
            date=datetime.fromisoformat(
                cast(str, hoursallocation["timesheet"]["date_event_registration"][0]["value"]),
            ).date(),
            hours_type=cast(str, hoursallocation["timesheet"]["type"]["label"]),
            hours=cast(float, hoursallocation["timesheet"]["timesheets_hours"][0]["value"]),
            namelike_id_employee=cast(str, hoursallocation["person"]["namelike_id_employee"][0]["value"]),
            namelike_id_ubw=namelike_id_ubw,
            namelike_name=cast(str, hoursallocation["subproject"]["namelike_name"][0]["value"]),
            project_type_name_powerbi=projecttypeinfo.project_type_name_powerbi,
        )

    # TODO: Move to front-end.
    async def export_powerbi_timesheets(self) -> AsyncGenerator[ExportPowerbiTimesheet, None]:
        async with self.dataaccessor_typedb as connectiontypedb:
            with as_file(
                files(knowledgeplatformmanagement_han).joinpath("timesheets.tql"),
            ) as path_file_query_timesheets:
                exportpowerbitimesheets_json = connectiontypedb.fetch(
                    path_file_query=Path(path_file_query_timesheets),
                )
            async for hoursallocation in exportpowerbitimesheets_json:
                yield self._export_powerbi_timesheet(hoursallocation=hoursallocation)

    # TODO: Move to front-end.
    async def export_powerbi_persons(self) -> AsyncGenerator[ExportPowerbiPerson, None]:
        async with self.dataaccessor_typedb as connectiontypedb:
            with as_file(files(knowledgeplatformmanagement_han).joinpath("persons.tql")) as path_file_query_persons:
                persons = connectiontypedb.fetch(
                    path_file_query=Path(path_file_query_persons),
                )
            async for person in persons:
                namelike_first = cast(str, person["person"]["namelike_first"][0]["value"])
                namelike_last = cast(str, person["person"]["namelike_last"][0]["value"])
                namelike_full = f"{namelike_first} {namelike_last}"
                exportpowerbiperson = ExportPowerbiPerson(
                    namelike_id_employee=cast(str, person["person"]["namelike_id_employee"][0]["value"]),
                    namelike_full=namelike_full,
                )
                if len(person["person"]["employmentcontract_ftepercentage"]) > 0:
                    exportpowerbiperson.employmentcontract_ftepercentage = person["person"][
                        "employmentcontract_ftepercentage"
                    ][0]["value"]
                if len(person["person"]["namelike_id_ubwcostcentre"]) > 0:
                    exportpowerbiperson.namelike_id_ubwcostcentre = person["person"]["namelike_id_ubwcostcentre"][0][
                        "value"
                    ]
                yield exportpowerbiperson
