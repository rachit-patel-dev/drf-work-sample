import inspect
from typing import Dict, Union

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


class APIResponse:
    """
    APIResponse class represents a custom response builder for API endpoints.

    Attributes:
        - message: Union[str, dict] - The message associated with the response.
        - errors: dict - Any errors associated with the response.
        - status_code: status - The HTTP status code of the response.
        - data: dict - The data associated with the response.
        - for_error: bool - Indicates if the response is for an error event.
        - general_error: bool - Indicates if the response is a general error.

    Methods:
        - __new__: Creates a new instance of the APIResponse class and returns the generated response.
        - __init__: Initializes the APIResponse instance with the provided parameters.
        - response_builder_callback: Determines the appropriate response based on the value of the 'for_error' attribute.
        - struct_response: Constructs a response dictionary based on the provided parameters.
        - success_message: Generates a success message based on the caller function name.
        - success: Creates a custom response for a success event.
        - fail: Creates a custom response for a failure event.

    Note:
        - The APIResponse class is designed to be used as a base class for creating custom response builders for specific API endpoints.
        - The success and fail methods can be overridden in subclasses to customize the response behavior.
        - The struct_response method can also be overridden to modify the structure of the response dictionary.

    """

    def __new__(
        cls,
        errors={},
        status_code: status = None,
        data: dict = {},
        message: Union[str, Dict[str, str]] = "",
        for_error: bool = False,
        general_error: bool = False,
    ) -> "APIResponse":
        cls.__init__(
            cls,
            message=message,
            errors=errors,
            status_code=status_code,
            data=data,
            for_error=for_error,
            general_error=general_error,
        )
        instance = super().__new__(cls)
        instance.message = message
        instance.errors = errors
        instance.status_code = status_code
        instance.data = data
        instance.for_error = for_error
        instance.caller_function = inspect.stack()[1].function
        return instance.response_builder_callback()

    def __init__(
        self,
        message: Union[str, dict],
        errors={},
        status_code: status = None,
        data: dict = {},
        for_error: bool = False,
        general_error: bool = False,
    ) -> None:
        self.message = message
        self.errors = errors
        self.status_code = status_code
        self.data = data
        self.for_error = for_error
        self.caller_function = inspect.stack()[1].function
        self.general_error = general_error

    def response_builder_callback(self):
        """
        This method determines the appropriate response based on the value of the 'for_error' attribute. If 'for_error' is True, it calls the 'fail' method to create a custom response for a failure event. If 'for_error' is False, it calls the 'success' method to create a custom response for a success event. The generated response is then returned.

        Returns:
            - If 'for_error' is True, a custom response for a failure event.
            - If 'for_error' is False, a custom response for a success event.

        """
        if self.for_error:
            return self.fail()
        else:
            return self.success()

    def struct_response(
        self, data: dict, success: bool, message: str, errors=None
    ) -> dict:
        """
        This method constructs a response dictionary based on the provided parameters. The response dictionary includes the following keys:
        - 'success': a boolean indicating the success status of the response.
        - 'message': a string representing the message associated with the response.
        - 'data': a dictionary containing the data associated with the response.
        - 'errors' (optional): a dictionary containing any errors associated with the response.

        Parameters:
        - data (dict): The data to be included in the response.
        - success (bool): The success status of the response.
        - message (str): The message associated with the response.
        - errors (dict, optional): Any errors associated with the response. Defaults to None.

        Returns:
        - dict: The constructed response dictionary.

        """
        response = dict(success=success, message=message, data=data)
        if errors:
            response["errors"] = errors
        return response

    def success_message(self) -> str:
        """
        This method generates a success message based on the caller function name. It replaces underscores in the function name with hyphens and capitalizes the first letter of each word. The generated success message is then returned.

        Returns:
            - str: The generated success message.

        """
        return f'{self.caller_function.replace("_", "-").title()} Successful.'

    def success(self) -> Response:
        """This method will create custom response for success event with response status 200."""
        success_message = self.message if self.message else self.success_message()
        response_data = self.struct_response(
            data=self.data, success=True, message=success_message
        )
        success_status = self.status_code if self.status_code else status.HTTP_200_OK
        return Response(response_data, status=success_status)

    def fail(self) -> Response:
        """This method will create custom response for failure event with custom response status."""
        error_message = (
            self.message[next(iter(self.message))][0]
            if isinstance(self.message, dict)
            else self.message
        )
        if self.general_error:
            error_message = settings.GENERAL_ERROR_MESSAGE
        response_data = self.struct_response(
            data={}, success=False, message=error_message, errors=self.errors
        )
        return Response(response_data, status=self.status_code)
