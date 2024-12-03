from rest_framework.pagination import PageNumberPagination


class KPIPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_modified_paginated_response(self, data, extra_kwargs: dict = {}):
        response_data = super().get_paginated_response(data).data
        if extra_kwargs:
            response_data.update(extra_kwargs)
        return response_data
