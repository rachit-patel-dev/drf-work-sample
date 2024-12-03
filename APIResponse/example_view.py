from django.conf import settings
from drf_spectacular.utils import extend_schema_view

# app imports
from focus_power.application.objective.services import ObjectiveAppServices
from focus_power.infrastructure.custom_response.response_and_error import APIResponse
from focus_power.interface.access_control.middleware_adapter import (
    get_access_controller,
)
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from . import open_api
from .filters import ObjectiveFilters
from .pagination import ObjectivePagination

# local imports
from .serializers import ObjectiveRetrieveSerializer


@extend_schema_view(
    create=open_api.objective_create_extension,
    update=open_api.objective_update_extension,
    list=open_api.objective_list_extension,
    retrieve=open_api.objective_retrieve_extension,
    list_conditions=open_api.list_conditions_extension,
    delete_condition=open_api.delete_condition_extension,
    add_condition=open_api.add_condition_extension,
    list_responsible_persons=open_api.responsible_person_extension,
    edit_condition=open_api.update_condition_extension,
    archive=open_api.objective_archive_extension,
)
class ObjectiveViewSet(viewsets.ViewSet):
    """
    API endpoints to create,list objectives
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = ObjectivePagination
    filter_class = ObjectiveFilters

    access_control = get_access_controller()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"log": self.log})
        return context

    @access_control()
    def create(self, request):
        """
        Create a new objective.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object containing the created objective data or error message.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an exception related to lazy loading.
        - Exception: If there is a general exception.

        """
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                objectives_app_services = ObjectiveAppServices()
                (
                    objective_obj,
                    serializer_context,
                ) = objectives_app_services.create_objective_from_dict(
                    data=serializer.data,
                    user=self.request.user,
                    company_id=self.request.query_params.get("company_id"),
                    is_success_manager=self.request.is_success_manager,
                )
                serializer_context.update(
                    {
                        "user": self.request.user,
                        "request": self.request,
                        "log": self.log,
                    }
                )
                response = ObjectiveRetrieveSerializer(
                    objective_obj, context=serializer_context
                )
                return APIResponse(
                    data=response.data, message="Successfully created objective"
                )
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=e.message,
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message="An error occurred while creating objective",
                    for_error=True,
                )
            except Exception as e:
                return APIResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    errors=e.args,
                    for_error=True,
                    general_error=True,
                )
        return APIResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=serializer.errors,
            message="Invalid data",
            for_error=True,
        )
