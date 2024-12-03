from django.utils import timezone
from focus_power.application.kpi.services import (
    KPIAppServices,
    KPIFrequencyAppServices,
    RelativeKPIAppServices,
)
from focus_power.application.user.services import UserAppServices
from focus_power.domain.calender_manager.models import CalenderManager
from focus_power.domain.kpi.kpi_frequency.models import KPIFrequency
from focus_power.domain.kpi.models import KPI, RelativeKPI

# django imports
from rest_framework import serializers


class KpiArchiveSerializer(serializers.Serializer):
    kpis = serializers.ListField(
        child=serializers.CharField(max_length=250, required=True)
    )
    archive = serializers.BooleanField(default=True)


class BaseRelativeKPISerializer(serializers.ModelSerializer):
    class Meta:
        model = RelativeKPI
        fields = "__all__"


class RelativeKPIRetrieveSerializer(BaseRelativeKPISerializer):
    class Meta(BaseRelativeKPISerializer.Meta):
        fields = ["absolute_kpi_id", "level"]


class RelativeKPIListSerializer(BaseRelativeKPISerializer):
    absolute_kpi = serializers.SerializerMethodField()

    def get_absolute_kpi(self, obj):
        absolute_kpi_app_services = KPIAppServices()
        absolute_kpi_obj = (
            absolute_kpi_app_services.list_absolute_kpis(user=self.context["user"])
            .filter(id=obj.absolute_kpi_id)
            .first()
        )

        # reporting person list
        user_app_service = UserAppServices()
        reporting_person_list = list(
            user_app_service.list_users()
            .filter(id=absolute_kpi_obj.reporting_person_id)
            .values("id", "first_name", "last_name", "profile_image")
        )
        reporting_person_dict = {user.get("id"): user for user in reporting_person_list}
        self.context.update({"reporting_person_dict": reporting_person_dict})

        return AbsoluteKPIRetrieveSerializer(
            absolute_kpi_obj,
            context=self.context,
        ).data

    class Meta:
        model = RelativeKPI
        exclude = ["absolute_kpi_id"]


class CalenderManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalenderManager
        fields = ["id", "data"]


class KPIFrequencyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIFrequency
        fields = "__all__"

    extra_kwargs = {
        "daily_data": {"required": False},
        "weekly_data": {"required": False},
        "monthly_data": {"required": False},
    }


class KPICreateSerializer(serializers.ModelSerializer):
    kpi_frequencies = serializers.ListField(
        child=serializers.JSONField(required=True), required=True
    )
    absolute_kpis = RelativeKPIRetrieveSerializer(many=True)
    calender_manager_id = serializers.CharField(max_length=250, allow_null=True)
    plan_frequency = serializers.ChoiceField(
        choices=KPI.FREQUENCY_TYPES, allow_null=True, allow_blank=True
    )
    year = serializers.IntegerField()

    def validate_year(self, value):
        unit_type = self.initial_data.get("unit_type")
        current_year = timezone.now().year
        # Commented the current year validation as
        # need to get the multiple year in KPI
        # if value < current_year and unit_type == KPI.ABSOLUTE:
        #     raise serializers.ValidationError(
        #         "Year must not be less than the current year."
        #     )
        return value

    def validate_calender_manager_id(self, value):
        unit_type = self.initial_data.get("unit_type")
        if unit_type == KPI.ABSOLUTE and value == None:
            raise serializers.ValidationError(
                f"calender_manager_id is required for {KPI.ABSOLUTE} KPI."
            )
        return value

    def validate_plan_frequency(self, value):
        unit_type = self.initial_data.get("unit_type")
        if unit_type == KPI.ABSOLUTE and value == None:
            raise serializers.ValidationError(
                f"plan_frequency is required for {KPI.ABSOLUTE} KPI."
            )
        return value

    class Meta:
        model = KPI
        fields = [
            "name",
            "reporting_person_id",
            "unit_type",
            "frequency",
            "logic_level",
            "unit",
            "kpi_frequencies",
            "absolute_kpis",
            "calender_manager_id",
            "plan_frequency",
            "year",
        ]
        extra_kwargs = {
            "absolute_kpis": {"required": False},
            "plan_frequency": {"required": False},
            "year": {"required": False},
            "calender_manager_id": {"required": False},
        }


class KPIListSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        exclude = ["reporting_person_id", "created_at", "modified_at"]


class AbsoluteKPIRetrieveSerializer(serializers.ModelSerializer):
    reporting_person = serializers.SerializerMethodField()
    monthly_target = serializers.SerializerMethodField()
    monthly_actual = serializers.SerializerMethodField()
    monthly_percentage = serializers.SerializerMethodField()
    ytd_target = serializers.SerializerMethodField()
    ytd_actual = serializers.SerializerMethodField()
    ytd_percentage = serializers.SerializerMethodField()
    parent_id = serializers.CharField(required=False)
    level = serializers.CharField(required=False)

    def get_calculation_data(self, obj):
        self.kpi_frequency_app_service = KPIFrequencyAppServices(
            user=self.context["user"],
            context=self.context,
            kpi_obj=obj,
        )
        self.kpi_frequency_app_service.set_target_month_and_target_date()
        calculation_data = {
            "monthly_target": 0,
            "monthly_actual": 0,
            "monthly_percentage": 0,
            "ytd_target": 0,
            "ytd_actual": 0,
            "ytd_percentage": 0,
        }
        return self.kpi_frequency_app_service.calculate_total_calculation_data_of_kpis(
            calculation_data=calculation_data
        )

    def get_monthly_target(self, obj):
        self.kpi_frequency_app_service = KPIFrequencyAppServices(
            user=self.context["user"],
            context=self.context,
            kpi_obj=obj,
        )
        self.kpi_frequency_app_service.set_target_month_and_target_date()
        return self.kpi_frequency_app_service.calculate_total_monthly_target()

    def get_monthly_actual(self, obj):
        return self.kpi_frequency_app_service.calculate_total_monthly_actual()

    def get_monthly_percentage(self, obj):
        return self.kpi_frequency_app_service.calculate_total_monthly_percentage()

    def get_ytd_target(self, obj):
        return self.kpi_frequency_app_service.calculate_total_ytd_target()

    def get_ytd_actual(self, obj):
        return self.kpi_frequency_app_service.calculate_total_ytd_actual()

    def get_ytd_percentage(self, obj):
        return self.kpi_frequency_app_service.calculate_total_ytd_percentage()

    def get_reporting_person(self, obj):
        if obj:
            reporting_person_context = self.context.get("reporting_person_dict", None)
            return reporting_person_context.get(obj.reporting_person_id)

    class Meta:
        model = KPI
        exclude = ["reporting_person_id"]


class CalculationBasedKPISerializer(AbsoluteKPIRetrieveSerializer):
    children = serializers.SerializerMethodField()
    level = serializers.CharField(required=False)

    def get_children(self, obj):
        related_kpi_app_service = RelativeKPIAppServices()
        related_kpis_queryset = related_kpi_app_service.list_relative_absolute_kpis(
            kpi_id=obj.id, user=self.context["user"]
        )
        if related_kpis_queryset:
            return AbsoluteKPIRetrieveSerializer(
                related_kpis_queryset,
                many=True,
                context=self.context,
            ).data
        else:
            return False

    def to_representation(self, instance):
        representation = super(CalculationBasedKPISerializer, self).to_representation(
            instance
        )
        if representation.get("unit_type") == KPI.ABSOLUTE:
            del representation["children"]
        else:
            representation.update({"level": "parent"})
        return representation


class KPIRetrieveSerializer(CalculationBasedKPISerializer):
    permissions = serializers.JSONField()

    def to_representation(self, instance):
        representation = super(KPIRetrieveSerializer, self).to_representation(instance)
        return representation


class KPIfrequencyUpdateSerializer(serializers.Serializer):
    VALUE_TYPE_CHOICES = (("actual", "actual"), ("target", "target"))
    kpi_frequencies = serializers.ListField(
        child=serializers.JSONField(required=True), required=True
    )
    value_type = serializers.ChoiceField(choices=VALUE_TYPE_CHOICES, required=True)


class KPIReportingPersonUpdateSerializer(serializers.Serializer):
    reporting_person = serializers.CharField(max_length=250, required=True)


class UpdateNumeratorOrDenominatorSerializer(serializers.Serializer):
    numerator = serializers.CharField(max_length=250, required=False)
    denominator = serializers.CharField(max_length=250, required=False)


class KPIUpdateSerializer(serializers.ModelSerializer):
    VALUE_TYPE_CHOICES = (("target", "target"),)
    value_type = serializers.ChoiceField(choices=VALUE_TYPE_CHOICES, required=False)
    absolute_kpis = UpdateNumeratorOrDenominatorSerializer(
        allow_null=True, required=False
    )
    kpi_frequencies = serializers.ListField(
        child=serializers.JSONField(required=True), required=False
    )

    class Meta:
        model = KPI
        fields = [
            "name",
            "unit",
            "logic_level",
            "frequency",
            "plan_frequency",
            "kpi_frequencies",
            "value_type",
            "absolute_kpis",
        ]
        extra_kwargs = {
            "name": {"required": False},
            "unit": {"required": False},
            "logic_level": {"required": False},
            "frequency": {"required": False},
            "plan_frequency": {"required": False},
            "kpi_frequencies": {"required": False},
            "value_type": {"required": False},
            "absolute_kpis": {"required": False},
        }
