# pytyhon imports
import logging

from focus_power.application.direct_report.services import DirectReportAppServices
from focus_power.infrastructure.custom_response.response_and_error import APIResponse

# app imports
from focus_power.infrastructure.logger.models import AttributeLogger

# django imports
from rest_framework import status
from utils.django.exceptions import MiddlewareException

from .middleware_services import MiddlewareServices


class UacMiddleware:
    def __init__(self, get_response, *args, **kwargs):
        self.direct_report_required = kwargs.get("direct_report_required", False)
        self.success_manager_required = kwargs.get("success_manager_required", True)
        self.get_response = get_response
        self.role = args

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, viewset, view_func, view_args, view_kwargs):
        pass


class MiddlewareWithLogger(UacMiddleware):
    def process_view(self, viewset, view_func, view_args, view_kwargs):
        log = AttributeLogger(logging.getLogger(__name__))
        viewset.log: AttributeLogger = log.with_attributes(
            user_id=viewset.request.user.id
        )

        # # check user_role for success manager
        middleware_services = MiddlewareServices()
        user_is_success_manager = middleware_services.check_user_is_success_manager(
            user_id=viewset.request.user.id
        )

        # default is_success_manager = False
        viewset.request.is_success_manager = False

        if user_is_success_manager:
            viewset.request.is_success_manager = True
            if self.success_manager_required and not viewset.request.query_params.get(
                "company_id"
            ):
                return APIResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    errors={},
                    message="Company is required for success managers.",
                    for_error=True,
                )

        if self.direct_report_required:
            if not viewset.request.query_params.get("direct_report"):
                return APIResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    errors={},
                    message="Direct report is required.",
                    for_error=True,
                )
            else:
                direct_report_id = viewset.request.query_params.get("direct_report")
                direct_report_app_service = DirectReportAppServices()
                direct_report = direct_report_app_service.get_direct_report_by_id(
                    direct_report_id=direct_report_id
                )
                if not direct_report:
                    return APIResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        errors={},
                        message="Direct report does not found.",
                        for_error=True,
                    )
        return super().process_view(viewset, view_func, view_args, view_kwargs)

    def process_exception(self, viewset, exception):
        viewset.log.debug(
            "Middleware has caught an exception. exception={}".format(str(exception))
        )
        print("middllware-------------process_exception---")

        if type(exception) == MiddlewareException:
            return APIResponse(
                status_code=exception.status_code,
                errors=exception.error_data(),
                message="Unauthorized Access",
                for_error=True,
            )
