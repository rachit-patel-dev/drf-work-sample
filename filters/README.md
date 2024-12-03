# KPIFilters Class - Django Filters for KPI Model

## Description

The code snippet defines a class called `KPIFilters` that provides filters for the KPI model using the `django_filters` library. It includes methods for filtering the queryset based on specific fields such as frequency, year, responsible person, and sorting.

## Inputs

- **queryset**: The queryset to be filtered.
- **name**: The name of the filter being applied.
- **value**: The value used for filtering.

## Flow

1. The `KPIFilters` class is defined, inheriting from `django_filters.FilterSet`.
2. The `Meta` class is defined within `KPIFilters` to specify the model and fields for the filters.
3. Filter fields are defined using `django_filters.CharFilter` and `django_filters.NumberFilter`, specifying the method to be used for filtering and the label for the filter.
4. Methods are defined for each filter, applying corresponding filtering logic to the queryset.
   - `frequency_filter`: Filters the queryset based on the frequency field by splitting the input value and filtering for matching frequencies.
   - `year_filter`: Filters the queryset based on the created_at year.
   - `responsible_person_filter`: Filters the queryset based on the reporting_person_id field by splitting the input value and filtering for matching responsible person IDs.
   - `sort_by_filter`: Sorts the queryset based on the given value.

## Outputs

The filtered/sorted queryset.

## Usage Example

```python
# Create an instance of KPIFilters, providing request.GET parameters and the KPI model queryset
filters = KPIFilters(data=request.GET, queryset=KPI.objects.all())

# Get the filtered queryset
filtered_queryset = filters.qs
```

In this example, the `KPIFilters` class is used to filter the KPI model queryset based on the GET parameters in a request. The resulting filtered queryset is stored in `filtered_queryset`.
```