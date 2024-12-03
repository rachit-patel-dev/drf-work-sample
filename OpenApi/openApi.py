# in open_api.py

divisions_tags = ["Division-Module"]

search_filter_param = OpenApiParameter(
    name="search",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Search value.",
)

pagination_param = OpenApiParameter(
    name="pagination",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The bool pagination paramter to exlude the pagination.",
)

divisions_list_extension = custom_extend_schema(
    tags=divisions_tags,
    parameters=[search_filter_param, pagination_param],
    responses={200: CompanyDivisionRetrieveSerializer},
    paginator=True,
)

divisions_create_extension = custom_extend_schema(
    tags=divisions_tags,
    request=CompanyDivisionCreateSerializer,
    responses={201: CompanyDivisionRetrieveSerializer},
)


# in views.py
@extend_schema_view(
    list_divisions=open_api.divisions_list_extension,
    create_division=open_api.divisions_create_extension,
)
class DivisionViewSet(viewsets.ViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = DivisionPagination
    filter_class = DivisionFilters

    access_control = get_access_controller()


# in urls.py
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


# in settings.py
SPECTACULAR_SETTINGS = {
    "TITLE": "FocusPower",
    "DESCRIPTION": "An application built to showcase a loose Domain Driven Design implementation in Django",
    "TOS": None,
    # Optional: MAY contain "name", "url", "email"
    "CONTACT": {"name": "", "email": ""},
    "VERSION": "0.1.0",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
}
