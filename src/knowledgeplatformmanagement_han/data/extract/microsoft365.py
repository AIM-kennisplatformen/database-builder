from pprint import pformat

from azure.identity import InteractiveBrowserCredential
from httpx import AsyncClient, Timeout
from kiota_authentication_azure.azure_identity_authentication_provider import AzureIdentityAuthenticationProvider
from loguru import logger
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder
from msgraph.generated.groups.item.group_item_request_builder import GroupItemRequestBuilder
from msgraph.generated.groups.item.transitive_members.transitive_members_request_builder import (
    TransitiveMembersRequestBuilder,
)
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.graph_request_adapter import GraphRequestAdapter
from msgraph.graph_service_client import GraphServiceClient

from knowledgeplatformmanagement_han.data.dao.datasink_microsoft365 import DatasinkMicrosoft365
from knowledgeplatformmanagement_han.data.model.personmicrosoft365 import PersonMicrosoft365


class Microsoft365:
    def __init__(
        self,
        datasink: DatasinkMicrosoft365,
        microsoft365_id_client: str | None,
        microsoft365_id_tenant: str | None,
        microsoft365_scopes_user: list[str],
    ) -> None:
        self.datasink = datasink
        self._microsoft365_scopes_user = microsoft365_scopes_user
        if microsoft365_id_client and microsoft365_id_tenant and microsoft365_scopes_user:
            self._interactivebrowsercredential = InteractiveBrowserCredential(
                authority="login.microsoft.com",
                client_id=microsoft365_id_client,
                prompt="login",
                # TODO: parameterize
                redirect_uri="http://localhost:8080",
                tenant_id=microsoft365_id_tenant,
            )
            asyncclient = AsyncClient(http1=False, http2=True, timeout=Timeout(60.0 * 30), follow_redirects=True)
            azureidentityauthenticationprovider = AzureIdentityAuthenticationProvider(
                self._interactivebrowsercredential,
                scopes=self._microsoft365_scopes_user,
            )
            self._graphserviceclient: GraphServiceClient = GraphServiceClient(
                credentials=self._interactivebrowsercredential,
                scopes=self._microsoft365_scopes_user,
                request_adapter=GraphRequestAdapter(
                    auth_provider=azureidentityauthenticationprovider,
                    client=asyncclient,
                ),
            )

    async def get_user_indepth(self, user_id: str) -> User | None:
        select_expertise = [
            "givenName",
            "id",
            "interests",
            "mail",
            "responsibilities",
            "schools",
            "skills",
            "surname",
        ]
        queryparameters = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(select=select_expertise)
        requestconfiguration = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=queryparameters,
        )
        try:
            return await self._graphserviceclient.users.by_user_id(user_id=user_id).get(
                request_configuration=requestconfiguration,
            )
        except ODataError:
            return None

    # The complexity is hard to avoid with the msgraph API.
    async def get_han_employees(self) -> None:  # noqa: C901, PLR0912
        logger.debug("Getting HAN employees ...")
        queryparameters_groupitem = GroupItemRequestBuilder.GroupItemRequestBuilderGetQueryParameters(
            select=[
                "id",
            ],
        )
        requestconfiguration_groupitem = GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(
            query_parameters=queryparameters_groupitem,
        )
        # HAN-MEDEWERKERS@hannl.onmicrosoft.com
        try:
            group = await self._graphserviceclient.groups.by_group_id(
                group_id="af9a4e2f-78e8-4e23-acd5-a059a2a44abe",
            ).get(
                request_configuration=requestconfiguration_groupitem,
            )
        except ODataError as exception:
            logger.exception(exception)
            raise
        if group is None:
            raise ValueError()
        queryparameters_transitivemembers = (
            TransitiveMembersRequestBuilder.TransitiveMembersRequestBuilderGetQueryParameters(
                count=True,
                select=["accountEnabled", "id", "userType"],
                filter="accountEnabled eq true and userType eq 'Member'",
                top=999,
            )
        )
        requestconfiguration_transitivemembers = (
            TransitiveMembersRequestBuilder.TransitiveMembersRequestBuilderGetRequestConfiguration(
                query_parameters=queryparameters_transitivemembers,
            )
        )
        requestconfiguration_transitivemembers.headers.add("ConsistencyLevel", "eventual")
        logger.debug("Processing group {} (ID: {}; {}) ...", group.display_name, group.id, group.mail)
        # The extensive branching is unavoidable with the msgraph API and semantics.
        # pylint: disable-next=too-many-nested-blocks
        if group.id:
            try:
                members = await self._graphserviceclient.groups.by_group_id(
                    group_id=group.id,
                ).transitive_members.graph_user.get(
                    request_configuration=requestconfiguration_transitivemembers,
                )
            except ODataError as exception:
                logger.exception(exception)
                raise
            # pylint: disable-next=while-used
            while members and members.odata_next_link:
                if isinstance(members, UserCollectionResponse) and members.value is not None:
                    for user in members.value:
                        if isinstance(user, User):
                            user_indepth = await self.get_user_indepth(user_id=user.id)
                            if user_indepth and user_indepth.given_name and user_indepth.surname and user_indepth.mail:
                                logger.trace(
                                    "Processing user {} {} <{}> ...",
                                    user_indepth.given_name,
                                    user_indepth.surname,
                                    user_indepth.mail,
                                )
                                if user_indepth is None:
                                    logger.warning(
                                        "Couldn’t find user with ID {id} (e-mail {mail}).",
                                        id=user.id,
                                        mail=user.mail,
                                    )
                                    continue
                                if (
                                    user_indepth.skills
                                    or user_indepth.interests
                                    or user_indepth.responsibilities
                                    or user_indepth.schools
                                ):
                                    logger.debug("User (ID: {}) has sufficient information in profile.", user.id)
                                    self.datasink.address_email_to_personmicrosoft365[user_indepth.mail] = (
                                        PersonMicrosoft365(
                                            address_email=user_indepth.mail,
                                            interests=user_indepth.interests,
                                            namelike_first=user_indepth.surname,
                                            namelike_last=user_indepth.given_name,
                                            responsibilities=user_indepth.responsibilities,
                                            schools=user_indepth.schools,
                                            skills=user_indepth.skills,
                                        )
                                    )
                            else:
                                logger.error(
                                    "Failed to fetch in-depth profile of user (ID: {id}).",
                                    id=user.id,
                                )
                        else:
                            logger.error(
                                "Non-User transitive member of group: {user}.",
                                user=pformat(user),
                            )
                try:
                    members = (
                        await self._graphserviceclient.groups.by_group_id(
                            group_id=group.id,
                        )
                        .transitive_members.graph_user.with_url(raw_url=members.odata_next_link)
                        .get(
                            request_configuration=requestconfiguration_transitivemembers,
                        )
                    )
                except ODataError as exception:
                    logger.exception(exception)
                    raise
