# django imports
from django.contrib.auth import login
from django.db import transaction
from drf_spectacular.utils import extend_schema_view
from rest_framework.response import Response
from rest_framework.views import APIView

# app imports
from taste_dna.application.user.services import UserAppServices

# local imports
from taste_dna.interface.user.social_auth.serializers.google_auth import (
    GoogleAuthSerializer,
)

from . import openapi


@extend_schema_view(
    post=openapi.google_auth_extension,
)
class GoogleAuthApiView(APIView):
    """
    API view for Google authentication.

    This class handles the POST request for Google authentication. It processes the request, validates the access token, and creates a user if necessary. If the authentication is successful, it logs in the user and returns a response with the user's token. If the authentication fails, it returns an error response.

    Attributes:
        post (method): Handles the POST request for Google authentication.

    Methods:
        post(request): Processes the POST request for Google authentication.

            Parameters:
                request (HttpRequest): The HTTP request object.

            Returns:
                Response: The HTTP response object.

            Raises:
                Exception: If an error occurs during the authentication process.
    """

    def post(self, request):
        """
        Process the POST request for Google authentication.

        Parameters:
        - request (HttpRequest): The HTTP request object.

        Returns:
        - Response: The HTTP response object.

        Raises:
        - Exception: If an error occurs during the authentication process.
        """
        with transaction.atomic():
            try:
                user_app_service = UserAppServices()
                serializer = GoogleAuthSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                access_token = serializer.validated_data["access_token"]
                created, user = user_app_service.create_user_from_google_auth(
                    access_token=access_token
                )
                if created and user:
                    login(request, user)
                    data = user_app_service.get_user_token(user=user)
                    return Response({"data": data})
                return Response({"error": "Authentication failed"})
            except Exception as e:
                return Response({"error": e.args})
