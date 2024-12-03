# lazy exceptions (lazy_exceptions.py)

import importlib
import inspect

from django.utils.functional import SimpleLazyObject
from focus_power.infrastructure.logger.models import AttributeLogger


# base exception with attribute logger
@dataclass(frozen=True)
class BaseExceptionWithLogs(Exception):
    item: str
    message: str
    log: AttributeLogger = None
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __post_init__(self):
        if not self.log:
            object.__setattr__(
                self, "log", AttributeLogger(logging.getLogger(__name__))
            )

    def error_data(self) -> dict:
        error_data = {"item": self.item, "message": self.message}
        self.log.error(str(error_data))

        return error_data

    def __str__(self):
        return "{}: {}".format(self.item, self.message)


# custom exceptions with status code
class Status401Exception(BaseExceptionWithLogs):
    def __init__(self, item, message, log):
        super().__init__(item, message, log, status_code=status.HTTP_401_UNAUTHORIZED)


class Status400Exception(BaseExceptionWithLogs):
    """
    Custom exception with a 400 status code.
    """

    def __init__(self, item, message, log):
        super().__init__(item, message, log, status_code=status.HTTP_400_BAD_REQUEST)


class Status403Exception(BaseExceptionWithLogs):
    def __init__(self, item, message, log):
        super().__init__(item, message, log, status_code=status.HTTP_403_FORBIDDEN)


class Status404Exception(BaseExceptionWithLogs):
    def __init__(self, item, message, log):
        super().__init__(item, message, log, status_code=status.HTTP_404_NOT_FOUND)


# custom exceptions with status code from base exception class


class UserSignUpException(base_exceptions.Status400Exception):
    pass


#
class UpdateStatusException(base_exceptions.Status400Exception):
    pass


class UserLoginException(base_exceptions.Status401Exception):
    pass


class UserNotExistException(base_exceptions.Status404Exception):
    pass


class UserProfileWithCompanyDetailsDoesNotExistException(
    base_exceptions.Status404Exception
):
    pass


class LazyExceptions:
    """
    LazyExceptions class.

    This class provides functionality for lazy loading of exceptions from a specified module.

    Methods:
    - get_all_classes(module_name): Returns a tuple of all classes in the specified module.
    - lazy_exceptions: Returns a tuple of lazy objects that represent the classes in the 'utils.django.exceptions' module.

    Example usage:
        lazy_exceptions = LazyExceptions().lazy_exceptions
        for lazy_exception in lazy_exceptions:
            print(lazy_exception)
    """

    def get_all_classes(self, module_name):
        """
        Returns a tuple of all classes in the specified module.

        Parameters:
        - module_name (str): The name of the module from which to retrieve the classes.

        Returns:
        tuple: A tuple containing all the classes found in the specified module.

        Example:
            lazy_exceptions = LazyExceptions()
            classes = lazy_exceptions.get_all_classes("utils.django.exceptions")
            for class_obj in classes:
                print(class_obj)
        """

        module = importlib.import_module(module_name)
        classes = inspect.getmembers(module, inspect.isclass)
        return tuple(class_obj for name, class_obj in classes)

    @property
    def lazy_exceptions(self):
        """
        Returns a tuple of lazy objects that represent the classes in the 'utils.django.exceptions' module.

        Returns:
        tuple: A tuple containing lazy objects that represent the classes found in the 'utils.django.exceptions' module.

        Example:
            lazy_exceptions = LazyExceptions().lazy_exceptions
            for lazy_exception in lazy_exceptions:
                print(lazy_exception)
        """
        return tuple(
            SimpleLazyObject(lambda: self.get_all_classes("utils.django.exceptions"))
        )


from utils.django.exceptions.lazy_exceptions import LazyExceptions

LAZY_EXCEPTIONS = LazyExceptions().lazy_exceptions


# use for raise exceptions in application or domain layer or from the business logic
def list_planning_overview_by_planning_id(
    self,
    user: User,
    planning_id: str,
    senior_id: str = None,
    serializer_context: dict = {},
) -> Tuple[QuerySet[PlanningOverview], dict]:

    raise UserNotExistException(
        "user-not-exist-exception", "User does not exist", self.log
    )


# use for catch the exceptions in interface layer


@extend_schema_view(
    list_calender_by_frequency=open_api.list_calender_listing,
    list_calender_weeks=open_api.list_calender_weeks,
)
class CalenderManagerViewSet(viewsets.ViewSet):
    """
    API endpoints to list calender data
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = CalenderManagerPagination

    access_control = get_access_controller()

    @action(detail=False, methods=["get"], name="list_calender_by_frequency")
    @access_control()
    def list_calender_by_frequency(self, request):
        """
        This code snippet is a method called 'list_calender_by_frequency' within a class.

        The method takes a 'request' object as a parameter and tries to generate calendar data based on the frequency and year provided in the request query parameters.

        If the generation is successful, it returns an APIResponse object with the generated calendar data and a success message.

        If an exception of type 'settings.LAZY_EXCEPTIONS' is raised, it catches the exception and returns an APIResponse object with the status code, error data, message, and a flag indicating it is an error response.

        If any other exception is raised, it catches the exception and returns an APIResponse object with a status code of 400, the exception arguments as errors, and flags indicating it is an error response and a general error.

        """
        try:
            calender_manager_app_services = CalenderManagerAppServices()
            calender_data = calender_manager_app_services.generate_calender_data_from_frequency_and_year(
                year=int(request.query_params.get("year")),
                frequency=request.query_params.get("frequency"),
                filters=self.week_name_filters_params(),
            )
            message = "Successfully listed all calender data."
            return APIResponse(data=calender_data, message=message)
        except settings.LAZY_EXCEPTIONS as ce:
            return APIResponse(
                status_code=ce.status_code,
                errors=ce.error_data(),
                message=ce.message,
                for_error=True,
            )
        except Exception as e:
            return APIResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=e.args,
                for_error=True,
                general_error=True,
            )
