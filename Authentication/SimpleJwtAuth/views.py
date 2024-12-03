from django.conf import settings

# django imports
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema_view

# app imports
from focus_power.application.user.services import UserAppServices
from focus_power.infrastructure.custom_response.response_and_error import APIResponse
from focus_power.interface.access_control.middleware_adapter import (
    get_access_controller,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException

from . import open_api

# local imports
from .serializers import (
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserLoginSerializer,
    UserSerializer,
    VerifyUserSerializer,
)


class BadRequest(APIException):
    status_code = 400
    default_detail = (
        "The request cannot be fulfilled, please try again with different parameters."
    )
    default_code = "bad_request"


@extend_schema_view(
    login=open_api.user_login_extension,
    forgot_password=open_api.user_forgot_password_extension,
    reset_password=open_api.user_reset_password_extension,
    verify_user=open_api.user_verify_user_extension,
)
class UserViewSet(viewsets.ViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    Methods:
    - get_queryset(): Retrieves the queryset of users.
    - get_serializer_context(): Retrieves the context for the serializer.
    - get_serializer_class(): Retrieves the serializer class based on the action.
    - login(request): Logs in a user with the provided email and password.
    - verify_user(request): Verifies a user based on the provided token.
    - sign_up(request): Signs up a new user.
    - forgot_password(request): Handles the forgot password functionality.
    - reset_password(request): Resets the password for a user.

    Raises:
    - settings.LAZY_EXCEPTIONS: If there is an error during the login, verification, sign-up, forgot password, or password reset process.
    - Exception: If there is a general error during the login, verification, sign-up, forgot password, or password reset process.
    """

    # lazy_exception_instance = LazyExceptions()
    access_control = get_access_controller()

    @access_control()
    def get_queryset(self):
        user_app_services = UserAppServices()
        return user_app_services.list_users().order_by("?")

    @access_control()
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"log": self.log})
        return context

    def get_serializer_class(self):
        if self.action == "login":
            return UserLoginSerializer
        if self.action == "verify_user":
            return VerifyUserSerializer
        if self.action == "forgot_password":
            return ForgotPasswordSerializer
        if self.action == "reset_password":
            return ResetPasswordSerializer
        return UserSerializer

    @action(detail=False, methods=["post"], name="login")
    @access_control()
    def login(self, request):
        """
        Logs in a user with the provided email and password.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object containing the login status and user data.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an error during the login process, such as invalid credentials, CEO not existing in the company, user company not found, etc.
        - Exception: If there is a general error during the login process.

        """
        serializer = self.get_serializer_class()
        serializer_data = serializer(data=request.data)
        if serializer_data.is_valid():
            email = serializer_data.data.get("email", None)
            password = serializer_data.data.get("password", None)
            try:
                user = authenticate(email=email, password=password)
                unauthorized_status_code = status.HTTP_401_UNAUTHORIZED
                error_message = None
                if not user:
                    error_message = "Email or password is invalid."
                elif not user.is_verified:
                    error_message = (
                        "Your account is not verified please verify it first."
                    )
                elif not user.is_active:
                    error_message = "Your account is not active.Contact to our support"
                if error_message:
                    return APIResponse(
                        status_code=unauthorized_status_code,
                        message=error_message,
                        for_error=True,
                    )
                response_data = UserAppServices().get_user_data_with_token(user=user)
                if response_data.get("is_verified") == False:
                    return APIResponse(
                        message="You are not verified. check your email to verify.",
                        status_code=unauthorized_status_code,
                        for_error=True,
                    )
                message = "You have logged in successfully"
                return APIResponse(data=response_data, message=message)
            except settings.LAZY_EXCEPTIONS as ule:
                message = "Email or password is invalid."
                return APIResponse(
                    status_code=ule.status_code,
                    errors=ule.error_data(),
                    message=message,
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as une:
                message = "CEO not exists in company"
                return APIResponse(
                    status_code=une.status_code,
                    errors=une.error_data(),
                    message=message,
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as exc:
                return APIResponse(
                    status_code=exc.status_code,
                    errors=exc.error_data(),
                    message=exc.message,
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as cnfe:
                message = "User Company not found."
                return APIResponse(
                    status_code=cnfe.status_code,
                    errors=cnfe.error_data(),
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
            errors=serializer_data.errors,
            message="Invalid Credentials",
            for_error=True,
        )

    @action(detail=False, methods=["post"], name="verify_user")
    @access_control()
    def verify_user(self, request):
        """
        Verifies a user based on the provided token.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object indicating the result of the verification process.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an error during the verification process.
        - Exception: If there is a general error during the verification process.
        """
        serializer = self.get_serializer_class()
        serializer_data = serializer(data=request.data)
        if serializer_data.is_valid():
            try:
                is_user_verified = UserAppServices().verify_token_for_new_user(
                    data=serializer_data.data
                )
                if is_user_verified:
                    return APIResponse(
                        data={},
                        message=f"Successfully verified user",
                    )
                else:
                    return APIResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message=f"An error occurred while verifying the user",
                        for_error=True,
                    )
            except settings.LAZY_EXCEPTIONS as use:
                return APIResponse(
                    status_code=use.status_code,
                    errors=use.error_data(),
                    message=f"An error occurred while verifying the user",
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
            errors=serializer_data.errors,
            message=f"This link is invalid try again",
            for_error=True,
        )

    @access_control()
    def sign_up(self, request):
        """
        Signs up a new user.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object indicating the result of the sign-up process.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an error during the sign-up process.
        - Exception: If there is a general error during the sign-up process.
        """
        serializer = self.get_serializer_class()
        serializer_data = serializer(data=request.data)
        if serializer_data.is_valid():
            try:
                user_data = UserAppServices().create_user_from_dict(
                    data=serializer_data.data
                )
                serialized_user_data = UserSerializer(
                    instance=user_data,
                    context={
                        "log": self.log,
                    },
                )
                return APIResponse(
                    status_code=status.HTTP_201_CREATED,
                    data=serialized_user_data.data,
                    message=f"Successfully sign-up for user.",
                )
            except settings.LAZY_EXCEPTIONS as use:
                return APIResponse(
                    status_code=use.status_code,
                    errors=use.error_data(),
                    message=f"An error occurred while Sign-up.",
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as uae:
                return APIResponse(
                    status_code=uae.status_code,
                    errors=uae.error_data(),
                    message=f"User already exists",
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as uae:
                return APIResponse(
                    status_code=uae.status_code,
                    errors=uae.error_data(),
                    message="Mail not sent.",
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
            errors=serializer_data.errors,
            message=f"Incorrect email or password",
            for_error=True,
        )

    @action(detail=False, methods=["post"], name="verify_user")
    @access_control()
    def forgot_password(self, request):
        """
        Forgot Password

        This method is used to handle the forgot password functionality. It takes a request object as a parameter and performs the following steps:
        1. Validates the serializer data.
        2. Calls the 'forgot_password' method of the 'UserAppServices' class to initiate the forgot password process.
        3. Returns an APIResponse object with a success message if the process is successful.
        4. Handles various exceptions that may occur during the process and returns an APIResponse object with appropriate error messages.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object indicating the result of the forgot password process.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an error during the forgot password process.
        - Exception: If there is a general error during the forgot password process.
        """
        serializer = self.get_serializer_class()
        serializer_data = serializer(data=request.data)
        if serializer_data.is_valid():
            try:
                UserAppServices().forgot_password(data=serializer_data.data)
                return APIResponse(
                    data={},
                    message=f"You have successfully requested for forgot-password",
                )
            except settings.LAZY_EXCEPTIONS as use:
                return APIResponse(
                    status_code=use.status_code,
                    errors=use.error_data(),
                    message="User does not exists",
                    for_error=True,
                )
            except settings.LAZY_EXCEPTIONS as uae:
                return APIResponse(
                    status_code=uae.status_code,
                    errors=uae.error_data(),
                    message="Mail not sent.",
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
            errors=serializer_data.errors,
            message=f"This link is invalid try again",
            for_error=True,
        )

    @action(detail=False, methods=["post"], name="reset_password")
    @access_control()
    def reset_password(self, request):
        """
        Resets the password for a user.

        This method is used to handle the password reset functionality. It takes a request object as a parameter and performs the following steps:
        1. Validates the serializer data.
        2. Calls the 'reset_password' method of the 'UserAppServices' class to reset the password.
        3. Returns an APIResponse object with a success message if the password reset is successful.
        4. Handles various exceptions that may occur during the process and returns an APIResponse object with appropriate error messages.

        Parameters:
        - request: The HTTP request object.

        Returns:
        - APIResponse: The response object indicating the result of the password reset process.

        Raises:
        - settings.LAZY_EXCEPTIONS: If there is an error during the password reset process.
        - Exception: If there is a general error during the password reset process.
        """
        serializer = self.get_serializer_class()
        serializer_data = serializer(data=request.data)
        if serializer_data.is_valid():
            try:
                is_reset_password = UserAppServices().reset_password(
                    data=serializer_data.data
                )
                if not is_reset_password:
                    return APIResponse(
                        status=status.HTTP_401_UNAUTHORIZED,
                        message="Your reset-password link is expired.Please try again",
                        for_error=True,
                    )
                return APIResponse(
                    data={},
                    message=f"You have successfully reset your password",
                )
            except settings.LAZY_EXCEPTIONS as use:
                return APIResponse(
                    status_code=use.status_code,
                    errors=use.error_data(),
                    message="Your reset-password link is expired.Please try again",
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
            errors=serializer_data.errors,
            message=f"This link is invalid try again",
            for_error=True,
        )
