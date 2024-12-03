from django.db import transaction
from drf_spectacular.utils import extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from taste_dna.application.user.services import User, UserAppServices
from utils.errors.response_errors import CustomResponse

from . import openapi


@extend_schema_view(
    post=openapi.apple_auth_extension,
)
class AppleLoginAPIView(APIView):
    """
    API View to login using Apple ID.

    Attributes:
        permission_classes (tuple): A tuple of permission classes for the view.

    Methods:
        post(request, format=None): Handles the POST request to create the data.

            Parameters:
                request (HttpRequest): The HTTP request object.
                format (str, optional): The format of the response data (default=None).

            Returns:
                Response: If the user with the given access token exists, returns a success response with the user token and a success message.
                        If the user with the given access token does not exist, creates a new user with the provided email, access token, and first name (if provided). Returns a success response with the user token and a success message.
                        If an error occurs during the login process, returns a failure response with an error message.

            Raises:
                None.

            Example Usage:
                POST /api/login/apple/ { "access_token": "abc123", "email": "example@example.com", "first_name": "John" }
    """

    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        POST method to create the data.

        Parameters:
        - request: The HTTP request object.
        - format: The format of the response data (default=None).

        Returns:
        - If the user with the given access token exists, returns a success response with the user token and a success message.
        - If the user with the given access token does not exist, creates a new user with the provided email, access token, and first name (if provided). Returns a success response with the user token and a success message.
        - If an error occurs during the login process, returns a failure response with an error message.

        Raises:
        - None.

        Example Usage:
        POST /api/login/apple/ { "access_token": "abc123", "email": "example@example.com", "first_name": "John" }

        """
        user_app_service = UserAppServices()
        message = "You have logged in successfully using Apple"
        with transaction.atomic():
            try:
                token = request.data.get("access_token")
                email = request.data.get("email")
                first_name = request.data.get("first_name", None)
                user_data = user_app_service.user_services.get_user_repo().filter(
                    apple_token=token
                )
                if user_data.exists():
                    user = user_data.get()
                    data = user_app_service.get_user_token(user=user)
                    return CustomResponse().success(data=data, message=message)
                instance = User()
                instance.email = email
                instance.apple_token = token
                instance.is_new_user = True
                instance.username = user_app_service.generate_username_from_email(
                    email=email
                )
                instance.first_name = first_name if first_name else instance.username
                instance.save()
                data = user_app_service.get_user_token(user=instance)
                return CustomResponse().success(data=data, message=message)
            except Exception:
                error_message = "An Error occurred while login using Apple."
                return Response(
                    {"status": "FAIL", "message": error_message, "data": []}
                )
