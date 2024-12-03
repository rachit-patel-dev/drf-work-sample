# Django Viewset for Division API

## Inputs
- `divisions_tags`: List of tags for categorizing API endpoints.
- `search_filter_param`: Query parameter for searching divisions by name.
- `pagination_param`: Query parameter for excluding pagination.
- `divisions_list_extension`: Extended schema for the list divisions endpoint.
- `divisions_create_extension`: Extended schema for the create division endpoint.

## Flow
1. Define variables `divisions_tags`, `search_filter_param`, and `pagination_param`.
2. Assign the result of `custom_extend_schema` to `divisions_list_extension`.
3. Assign the result of `custom_extend_schema` to `divisions_create_extension`.
4. Define `DivisionViewSet` class with authentication, permission, pagination, and filtering settings.
5. Use `extend_schema_view` decorator to extend the schema of `DivisionViewSet` with custom extensions.
6. Define URL patterns for Swagger documentation and Spectacular schema view.
7. Define Spectacular settings in the `SPECTACULAR_SETTINGS` dictionary.

## Outputs
- `divisions_list_extension`: Custom schema for the list divisions endpoint.
- `divisions_create_extension`: Custom schema for the create division endpoint.
- `DivisionViewSet`: Django viewset class for handling API endpoints related to divisions.

## Usage Example
```python
# Import necessary modules and classes
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from myapp.serializers import CompanyDivisionRetrieveSerializer, CompanyDivisionCreateSerializer
from myapp.pagination import DivisionPagination
from myapp.filters import DivisionFilters
from myapp.authentication import JWTAuthentication
from myapp.access_control import get_access_controller
from myapp import open_api

# Define the DivisionViewSet class
@extend_schema_view(
    list_divisions=open_api.divisions_list_extension,
    create_division=open_api.divisions_create_extension,
)
class DivisionViewSet(viewsets.ViewSet):
    """
    API endpoint that allows users to view or edit divisions.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = DivisionPagination
    filter_class = DivisionFilters

    access_control = get_access_controller()
```

## URLs (in `urls.py`)
```python
if settings.DEBUG:
    urlpatterns += [
        path(
            API_SWAGGER_URL,
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path("api/v0/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("__debug__/", include(debug_toolbar.urls)),
    ]
```

## Spectacular Settings (in `settings.py`)
```python
SPECTACULAR_SETTINGS = {
    "TITLE": "FocusPower",
    "DESCRIPTION": "An application built to showcase a loose Domain Driven Design implementation in Django",
    "TOS": None,
    "CONTACT": {"name": "", "email": ""},
    "VERSION": "0.1.0",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
}
```