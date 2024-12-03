from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer class for the User model.

    Attributes:
    - model (Model): The User model.
    - fields (tuple): The fields to include in the serialized representation of the User model.
    - extra_kwargs (dict): Additional keyword arguments for the fields, such as write_only for the password field.
    """

    class Meta:
        model = User
        fields = ("id", "username", "password")
        extra_kwargs = {"password": {"write_only": True}}


class AuthViews(APIView):
    """
    A class representing authentication views.

    This class provides two methods for user authentication: sign_up and login.

    Attributes:
    - None

    Methods:
    - sign_up: Signs up a new user.
    - login: Logs in a user.

    Example Usage:
        auth_views = AuthViews()
        auth_views.sign_up(request)
        auth_views.login(request)
    """

    @action(detail=False, methods=["post"], name="sign_up")
    def sign_up(self, request):
        """
        Signs up a new user.

        Parameters:
        - request (HttpRequest): The HTTP request object.

        Returns:
        - Response: The HTTP response object containing the token and user ID if the user is successfully signed up. Otherwise, it returns the validation errors.

        Raises:
        - None

        Example Usage:
        sign_up(request)
        """
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "user_id": user.id}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], name="login")
    def login(self, request):
        """
        Logs in a user.

        Parameters:
        - request (HttpRequest): The HTTP request object.

        Returns:
        - Response: The HTTP response object containing the token and user ID if the user is successfully logged in. Otherwise, it returns an error message indicating invalid credentials.

        Raises:
        - None

        Example Usage:
        login(request)
        """
        username = request.data.get("username")
        password = request.data.get("password")

        user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "user_id": user.id}, status=status.HTTP_200_OK
            )

        return Response(
            {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
