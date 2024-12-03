# Custom Pagination Classes and Viewset Example

## Description

The provided code snippet defines two custom pagination classes, `CalenderManagerPagination` and `KPIReportingPagination`, which extend the `PageNumberPagination` class from the `rest_framework.pagination` module. Additionally, it includes a method `get_modified_paginated_response` in the `KPIReportingPagination` class to return a modified paginated response. The code also showcases a viewset class, `KPIViewSet`, that uses the `KPIPagination` class for pagination and includes an action method, `absolute_kpi_list`, to list absolute KPIs.

## Inputs

- **request:** The HTTP request object.

## Flow

1. The `CalenderManagerPagination` and `KPIReportingPagination` classes define attributes (`page_size`, `page_size_query_param`, and `max_page_size`) to control pagination behavior.

2. The `get_modified_paginated_response` method in the `KPIReportingPagination` class modifies the paginated response by adding extra keyword arguments to the response data.

3. The `KPIViewSet` class includes the `pagination_class` attribute to specify the pagination class to be used.

4. The `absolute_kpi_list` method in the `KPIViewSet` class:
    - Retrieves a queryset of absolute KPIs.
    - Paginates the queryset using the `pagination_class`.
    - Serializes the paginated data.
    - Returns the paginated response.

## Outputs

Paginated response data containing the requested data and additional keyword arguments if provided.

## Usage Example

```python
# Create an instance of the KPIReportingPagination class
pagination = KPIReportingPagination()

# Retrieve the queryset of absolute KPIs
queryset = KPIReporting.objects.all()

# Paginate the queryset using the pagination class
paginated_queryset = pagination.paginate_queryset(queryset, request)

# Serialize the paginated queryset
serializer = KPIReportingSerializer(paginated_queryset, many=True)

# Get the modified paginated response with additional keyword arguments
response = pagination.get_modified_paginated_response(serializer.data, extra_kwargs={'total_count': total_count})

# Return the response as the API response
return response
```