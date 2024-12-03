from django.conf import settings
from drf_spectacular.utils import extend_schema_view
from focus_power.application.kpi.services import (
    KPIAppServices,
    KPIFrequencyAppServices,
    RelativeKPIAppServices,
)
from focus_power.infrastructure.custom_response.response_and_error import APIResponse
from focus_power.interface.access_control.middleware_adapter import (
    get_access_controller,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from utils.django.exceptions import KPIsException

from . import open_api

# local imports
from .filters import KPIFilters
from .pagination import KPIPagination
from .serializers import (
    CalculationBasedKPISerializer,
    KpiArchiveSerializer,
    KPICreateSerializer,
    KPIfrequencyUpdateSerializer,
    KPIListSerializer,
    KPIReportingPersonUpdateSerializer,
    KPIRetrieveSerializer,
    KPIUpdateSerializer,
    RelativeKPIListSerializer,
)

# app imports


@extend_schema_view(
    create=open_api.kpi_create_extension,
    absolute_kpi_list=open_api.absolute_kpi_listing,
    list=open_api.kpi_listing,
    retrieve=open_api.kpi_retrieve_extension,
    update_kpi=open_api.kpi_update,
    get_frequency_for_absolute_kpi=open_api.get_frequency_for_absolute_kpi,
    related_absolute_kpi_list=open_api.related_absolute_kpi_list,
    update_values_of_frequency_data=open_api.update_values_of_frequency_data,
    update_reporting_person=open_api.update_reporting_person,
    delete_kpi=open_api.delete_kpi,
    archive_kpi=open_api.archive_kpi,
)
class KPIViewSet(viewsets.ViewSet):
    """
    API endpoints to create,list KPIs
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = KPIPagination
    filter_class = KPIFilters
    access_control = get_access_controller()

    @access_control()
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"log": self.log})
        return context

    def get_serializer_class(self):
        if self.action == "create":
            return KPICreateSerializer
        if self.action == "absolute_kpi_list":
            return KPIListSerializer
        if self.action == "related_absolute_kpi_list":
            return RelativeKPIListSerializer
        if self.action == "list":
            return KPIRetrieveSerializer
        if self.action == "update_kpi":
            return KPIUpdateSerializer
        if self.action == "update_values_of_frequency_data":
            return KPIfrequencyUpdateSerializer
        if self.action == "update_reporting_person":
            return KPIReportingPersonUpdateSerializer
        if self.action == "archive_kpi":
            return KpiArchiveSerializer
        return CalculationBasedKPISerializer

    @access_control()
    def create(self, request):
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                kpi_app_services = KPIAppServices()
                (kpi_obj, _) = kpi_app_services.create_kpi_with_frequency_from_dict(
                    data=serializer.data,
                    user=self.request.user,
                    company_id=self.request.query_params.get("company_id"),
                )
                response_data = KPIListSerializer(
                    instance=kpi_obj,
                    context={
                        "request": self.request,
                        "log": self.log,
                        "user": self.request.user,
                    },
                ).data
                return APIResponse(
                    data=response_data,
                    message=f"Successfully created {serializer.data.get('unit_type')} KPI",
                )
            except settings.LAZY_EXCEPTIONS as e:
                message = (
                    "An error occurred while creating KPI."
                    if isinstance(e, KPIsException)
                    else e.message
                )
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=message,
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

    @action(detail=True, methods=["patch"], name="update_kpi")
    @access_control()
    def update_kpi(self, request, pk):
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                kpi_app_services = KPIAppServices()
                kpi_obj, serializer_context = kpi_app_services.update_kpi_from_dict(
                    kpi_id=pk,
                    data=serializer.data,
                    user=self.request.user,
                    company_id=self.request.query_params.get("company_id"),
                )
                year, month, last_date, current_week = kpi_app_services.get_last_date(
                    query_params=self.request.query_params
                )
                serializer_context.update(
                    {
                        "user": self.request.user,
                        "request": self.request,
                        "log": self.log,
                        "year": year,
                        "month": month,
                        "last_date": last_date,
                        "current_week": current_week,
                    }
                )
                response = CalculationBasedKPISerializer(
                    kpi_obj, context=serializer_context
                )
                return APIResponse(
                    data=response.data,
                    message="Successfully updated KPI",
                )
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=e.message,
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

    @action(detail=False, methods=["get"], name="absolute_kpi_list")
    @access_control()
    def absolute_kpi_list(self, request):
        kpi_app_services = KPIAppServices()
        serializer = self.get_serializer_class()
        queryset = kpi_app_services.list_absolute_kpis(
            user=self.request.user,
            company_id=self.request.query_params.get("company_id"),
        ).order_by("-created_at")
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer_data = serializer(
            paginated_queryset,
            many=True,
            context={
                "user": self.request.user,
                "request": self.request,
                "log": self.log,
            },
        )
        paginated_data = paginator.get_paginated_response(serializer_data.data).data
        message = "Successfully listed all absolute KPIs."
        return APIResponse(data=paginated_data, message=message)

    @access_control(direct_report_required=True)
    def list(self, request):
        try:
            serializer = self.get_serializer_class()
            kpi_app_services = KPIAppServices()
            direct_report_id = self.request.query_params.get("direct_report")
            queryset, serializer_context = kpi_app_services.list_kpi(
                user=self.request.user,
                direct_report_id=direct_report_id,
                company_id=self.request.query_params.get("company_id"),
            )
            filtered_queryset = self.filter_class(
                self.request.query_params, queryset=queryset
            ).qs
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(filtered_queryset, request)
            year, month, last_date, current_week = kpi_app_services.get_last_date(
                query_params=self.request.query_params
            )
            serializer_context.update(
                {
                    "user": self.request.user,
                    "request": self.request,
                    "log": self.log,
                    "year": year,
                    "month": month,
                    "last_date": last_date,
                    "current_week": current_week,
                }
            )
            serializer_data = serializer(
                paginated_queryset, many=True, context=serializer_context
            )
            paginated_data = paginator.get_modified_paginated_response(
                serializer_data.data, dict(current_week=current_week)
            )
            message = "Successfully listed all KPIs."
            return APIResponse(data=paginated_data, message=message)
        except settings.LAZY_EXCEPTIONS as une:
            return APIResponse(
                status_code=une.status_code,
                errors=une.error_data(),
                message=une.message,
                for_error=True,
            )
        except Exception as e:
            return APIResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=e.args,
                for_error=True,
                general_error=True,
            )

    @access_control()
    def retrieve(self, request, pk):
        try:
            kpi_app_services = KPIAppServices()
            kpi_obj, serializer_context = kpi_app_services.get_kpi_by_id(
                kpi_id=pk,
                user=self.request.user,
                company_id=self.request.query_params.get("company_id"),
            )
            year, month, last_date, current_week = kpi_app_services.get_last_date(
                query_params=self.request.query_params
            )
            serializer_context.update(
                {
                    "user": self.request.user,
                    "request": self.request,
                    "log": self.log,
                    "year": year,
                    "month": month,
                    "last_date": last_date,
                    "current_week": current_week,
                }
            )
            serializer = CalculationBasedKPISerializer(
                kpi_obj, context=serializer_context
            )
            return APIResponse(
                data=serializer.data, message="Successfully retrieved KPI"
            )
        except settings.LAZY_EXCEPTIONS as e:
            return APIResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                errors=e.error_data(),
                message=e.message,
                for_error=True,
            )
        except Exception as e:
            return APIResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=e.args,
                for_error=True,
                general_error=True,
            )

    @action(detail=True, methods=["get"], name="related_absolute_kpi_list")
    @access_control(success_manager_required=False)
    def related_absolute_kpi_list(self, request, pk):
        relative_kpi_app_service = RelativeKPIAppServices()
        serializer = self.get_serializer_class()
        queryset = relative_kpi_app_service.list_relative_kpis(
            user=self.request.user, kpi_id=pk
        ).order_by("-created_at")
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        kpi_app_services = KPIAppServices()
        year, month, last_date, current_week = kpi_app_services.get_last_date(
            query_params=self.request.query_params
        )
        serializer_data = serializer(
            paginated_queryset,
            many=True,
            context={
                "user": self.request.user,
                "request": self.request,
                "log": self.log,
                "year": year,
                "month": month,
                "last_date": last_date,
                "current_week": current_week,
            },
        )
        paginated_data = paginator.get_paginated_response(serializer_data.data).data
        message = "Successfully listed related absolute KPIs."
        return APIResponse(data=paginated_data, message=message)

    @action(detail=True, methods=["get"], name="update_absolute_kpi_actual_values")
    @access_control()
    def get_frequency_for_absolute_kpi(self, request, pk):
        try:
            kpi_frequency_app_service = KPIFrequencyAppServices(user=self.request.user)
            kpi_frequency_data = (
                kpi_frequency_app_service.get_kpi_frequency_data_by_kpi_id(
                    kpi_id=pk,
                    user=self.request.user,
                    filter_frequency=self.request.query_params.get("frequency"),
                    is_cumulative=self.request.query_params.get("is_cumulative")
                    == "true",
                    is_percentage=self.request.query_params.get("is_percentage")
                    == "true",
                    for_graph=self.request.query_params.get("for_graph") == "true",
                    for_bar=self.request.query_params.get("for_bar") == "true",
                    start_date=self.request.query_params.get("start_date"),
                    end_date=self.request.query_params.get("end_date"),
                    company_id=self.request.query_params.get("company_id"),
                )
            )
            message = "Successfully listed all frequency data for absolute KPI."
            return APIResponse(data=kpi_frequency_data, message=message)
        except settings.LAZY_EXCEPTIONS as e:
            return APIResponse(
                status_code=e.status_code,
                errors=e.error_data(),
                message=e.message,
                for_error=True,
            )
        except Exception as e:
            return APIResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=e.args,
                for_error=True,
                general_error=True,
            )

    @action(detail=True, methods=["put"], name="update_values_of_frequency_data")
    @access_control()
    def update_values_of_frequency_data(self, request, pk):
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                kpi_app_service = KPIAppServices()
                kpi_app_service.update_kpi_frequency_values(
                    data=serializer.data,
                    kpi_id=pk,
                    user=self.request.user,
                    filter_frequency=self.request.query_params.get("frequency"),
                    value_type=serializer.data.get("value_type"),
                    company_id=self.request.query_params.get("company_id"),
                )
                message = "Successfully updated actual values of absolute KPI."
                return APIResponse(data={}, message=message)
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=e.message,
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

    @action(detail=True, methods=["put"], name="update_reporting_person")
    @access_control()
    def update_reporting_person(self, request, pk):
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                kpi_app_service = KPIAppServices()
                kpi_obj, serializer_context = kpi_app_service.update_reporting_person(
                    pk,
                    data=serializer.data,
                    user=self.request.user,
                    company_id=self.request.query_params.get("company_id"),
                )
                year, month, last_date, current_week = kpi_app_service.get_last_date(
                    query_params=self.request.query_params
                )
                serializer_context.update(
                    {
                        "user": self.request.user,
                        "request": self.request,
                        "log": self.log,
                        "year": year,
                        "month": month,
                        "last_date": last_date,
                        "current_week": current_week,
                    }
                )
                response = CalculationBasedKPISerializer(
                    kpi_obj, context=serializer_context
                )
                return APIResponse(
                    data=response.data,
                    message="Successfully updated Responsible person.",
                )
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=e.message,
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

    @action(detail=False, methods=["patch"], name="archive_kpi")
    @access_control()
    def archive_kpi(self, request):
        get_serializer = self.get_serializer_class()
        serializer = get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                kpi_app_service = KPIAppServices()
                kpi_app_service.archive_kpi(
                    user=self.request.user,
                    kpi_list=serializer.data.get("kpis", []),
                    archive=serializer.data.get("archive", True),
                )
                return APIResponse(
                    data={},
                    message="Successfully archived KPI.",
                )
            except settings.LAZY_EXCEPTIONS as e:
                return APIResponse(
                    status_code=e.status_code,
                    errors=e.error_data(),
                    message=e.message,
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

    @action(detail=True, methods=["delete"], name="delete_kpi")
    @access_control()
    def delete_kpi(self, request, pk):
        try:
            kpi_app_service = KPIAppServices()
            kpi_app_service.delete_kpi(
                kpi_id=pk,
                user=self.request.user,
            )
            return APIResponse(
                data={},
                message="Successfully deleted KPI.",
            )
        except settings.LAZY_EXCEPTIONS as e:
            return APIResponse(
                status_code=e.status_code,
                errors=e.error_data(),
                message=e.message,
                for_error=True,
            )
        except Exception as e:
            return APIResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=e.args,
                for_error=True,
                general_error=True,
            )
