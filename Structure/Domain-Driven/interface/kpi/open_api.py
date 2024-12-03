from datetime import datetime

from drf_spectacular.utils import OpenApiExample, OpenApiParameter
from focus_power.domain.kpi.models import KPI
from utils.django.custom_extend_schema import custom_extend_schema

from .serializers import (
    CalculationBasedKPISerializer,
    KpiArchiveSerializer,
    KPICreateSerializer,
    KPIListSerializer,
)

kpi_tags = ["KPI-Module"]

frequency_filter_param = OpenApiParameter(
    name="frequency",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Year value.",
    examples=[
        OpenApiExample(
            "frequency",
            value=f"{KPI.YEARLY}, {KPI.MONTHLY}, {KPI.WEEKLY}, {KPI.QUARTERLY}, {KPI.DAILY}",
        )
    ],
)

is_cumulative_param = OpenApiParameter(
    name="is_cumulative",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Year value.",
    examples=[
        OpenApiExample(
            "is_cumulative",
            value="true",
        )
    ],
)

is_percentage_param = OpenApiParameter(
    name="is_percentage",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Percentage value.",
    examples=[
        OpenApiExample(
            "is_percentage",
            value="true",
        )
    ],
)

for_graph_param = OpenApiParameter(
    name="for_graph",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name for_graph value.",
    examples=[
        OpenApiExample(
            "for_graph",
            value="true",
        )
    ],
)

for_bar_param = OpenApiParameter(
    name="for_bar",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name for_bar value.",
    examples=[
        OpenApiExample(
            "for_bar",
            value="true",
        )
    ],
)

start_date_param = OpenApiParameter(
    name="start_date",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name start_date value.",
    examples=[
        OpenApiExample(
            "start_date",
            value=datetime.now(),
        )
    ],
)


end_date_param = OpenApiParameter(
    name="end_date",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name end_date value.",
    examples=[
        OpenApiExample(
            "end_date",
            value=datetime.now(),
        )
    ],
)
year = OpenApiParameter(
    name="year",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Year value.",
    examples=[OpenApiExample("year", value=datetime.now().year)],
)

month = OpenApiParameter(
    name="month",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name month value.",
    examples=[OpenApiExample("month", value=0)],
)

value_type_filter_param = OpenApiParameter(
    name="value_type",
    type=str,
    location=OpenApiParameter.QUERY,
    description="The name Year value.",
    examples=[OpenApiExample("value_type", value="target,actual")],
)

direct_report_param = OpenApiParameter(
    name="direct_report",
    type=str,
    location=OpenApiParameter.QUERY,
    description="logged in user's direct report id",
    examples=None,
)

kpi_responsible_person_param = OpenApiParameter(
    name="responsible_person",
    type=str,
    location=OpenApiParameter.QUERY,
    description="Param to filter the KPI by Reporting Person ID.",
)

kpi_sorting_param = OpenApiParameter(
    name="sort_by",
    type=str,
    location=OpenApiParameter.QUERY,
    description="kpi sorting",
    examples=[
        OpenApiExample(
            "sort_by",
            value="name, -name",
        ),
    ],
)

company_id = OpenApiParameter(
    name="company_id",
    type=str,
    location=OpenApiParameter.QUERY,
    description="filter with company_id for success-manager",
)


kpi_create_extension = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    request=KPICreateSerializer,
    responses={200: KPIListSerializer},
)
absolute_kpi_listing = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    responses={200: KPIListSerializer},
    paginator=True,
)
kpi_listing = custom_extend_schema(
    tags=kpi_tags,
    parameters=[year]
    + [month]
    + [direct_report_param]
    + [kpi_responsible_person_param]
    + [kpi_sorting_param]
    + [company_id],
    responses={200: CalculationBasedKPISerializer},
    paginator=True,
)

kpi_update = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    responses={200: CalculationBasedKPISerializer},
)

kpi_retrieve_extension = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    responses={200: CalculationBasedKPISerializer},
)

get_frequency_for_absolute_kpi = custom_extend_schema(
    tags=kpi_tags,
    parameters=[frequency_filter_param]
    + [is_cumulative_param]
    + [is_percentage_param]
    + [for_graph_param]
    + [start_date_param]
    + [end_date_param]
    + [for_bar_param]
    + [company_id],
    responses={200: {}},
)

related_absolute_kpi_list = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    responses={200: {}},
    paginator=True,
)


update_values_of_frequency_data = custom_extend_schema(
    tags=kpi_tags,
    parameters=[frequency_filter_param, company_id],
    responses={200: {}},
)

update_reporting_person = custom_extend_schema(
    tags=kpi_tags,
    parameters=[company_id],
    responses={200: CalculationBasedKPISerializer},
)

delete_kpi = custom_extend_schema(
    tags=kpi_tags,
    responses={200: {}},
)
archive_kpi = custom_extend_schema(
    tags=kpi_tags,
    request=KpiArchiveSerializer,
    responses={200: {}},
)
