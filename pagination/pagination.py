from rest_framework.pagination import PageNumberPagination


# custom pagination
class CalenderManagerPagination(PageNumberPagination):
    """
    Pagination class for the CalenderManager app.

    This class is used to paginate the results of the CalenderManager app. It extends the PageNumberPagination class from the rest_framework.pagination module.

    Attributes:
        page_size (int): The number of items to include in each page. Default is 5.
        page_size_query_param (str): The query parameter used to specify the page size. Default is "page_size".
        max_page_size (int): The maximum allowed page size. Default is 100.

    Methods:
        get_paginated_response(data): Returns a paginated response for the given data.
    """

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


class KPIReportingPagination(PageNumberPagination):
    """
    Pagination class for the KPIReporting app.

    This class is used to paginate the results of the KPIReporting app. It extends the PageNumberPagination class from the rest_framework.pagination module.

    Attributes:
        page_size (int): The number of items to include in each page. Default is 5.
        page_size_query_param (str): The query parameter used to specify the page size. Default is "page_size".
        max_page_size (int): The maximum allowed page size. Default is 100.

    Methods:
        get_modified_paginated_response(data, extra_kwargs): Returns a modified paginated response for the given data.

    Example usage:
        pagination = KPIReportingPagination()
        queryset = KPIReporting.objects.all()
        paginated_queryset = pagination.paginate_queryset(queryset, request)
        serializer = KPIReportingSerializer(paginated_queryset, many=True)
        response = pagination.get_modified_paginated_response(serializer.data, extra_kwargs={'total_count': total_count})
        return response
    """

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_modified_paginated_response(self, data, extra_kwargs: dict = {}):
        """
        Returns a modified paginated response for the given data.

        Parameters:
            data (list): The paginated data to be modified.
            extra_kwargs (dict, optional): Additional keyword arguments to be added to the response data. Default is an empty dictionary.

        Returns:
            dict: The modified paginated response data.

        Example:
            pagination = KPIReportingPagination()
            queryset = KPIReporting.objects.all()
            paginated_queryset = pagination.paginate_queryset(queryset, request)
            serializer = KPIReportingSerializer(paginated_queryset, many=True)
            response = pagination.get_modified_paginated_response(serializer.data, extra_kwargs={'total_count': total_count})
            return response
        """
        response_data = super().get_paginated_response(data).data
        if extra_kwargs:
            response_data.update(extra_kwargs)
        return response_data


# use of pagination
class KPIViewSet(viewsets.ViewSet):
    """
    API endpoints to create,list KPIs
    """

    pagination_class = KPIPagination

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
