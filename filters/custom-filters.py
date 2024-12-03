import django_filters
from django.db.models import Q
from focus_power.domain.kpi.models import KPI


class KPIFilters(django_filters.FilterSet):
    """
    A class that defines filters for the KPI model.

    Attributes:
        model (django.db.models.Model): The model that the filters are applied to.
        fields (list): The fields that the filters are applied to.

    Methods:
        frequency_filter(queryset, name, value): Filters the queryset based on the frequency field.
        year_filter(queryset, name, value): Filters the queryset based on the created_at year.
        responsible_person_filter(queryset, name, value): Filters the queryset based on the reporting_person_id field.
        sort_by_filter(queryset, name, value): Sorts the queryset based on the given value.

    """

    class Meta:
        model = KPI
        fields = ["frequency"]

    frequency = django_filters.CharFilter(method="frequency_filter", label="frequency")

    year = django_filters.NumberFilter(method="year_filter", label="Year")

    responsible_person = django_filters.CharFilter(
        method="responsible_person_filter", label="responsible_person"
    )

    sort_by = django_filters.CharFilter(method="sort_by_filter", label="sort_by")

    def frequency_filter(self, queryset, name, value):
        frequency = value.strip().split(",")
        return queryset.filter(Q(frequency__in=frequency)).distinct()

    def year_filter(self, queryset, name, value):
        return queryset.filter(created_at__year=value)

    def responsible_person_filter(self, queryset, name, value):
        responsible_person_ids = value.strip().split(",")
        return queryset.filter(
            Q(reporting_person_id__in=responsible_person_ids)
        ).distinct()

    def sort_by_filter(self, queryset, name, value):
        return queryset.order_by(value)
