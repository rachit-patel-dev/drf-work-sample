"""This is a model module to store KPI and RelativeKPI data in to the database"""

import uuid
from dataclasses import dataclass

from django.db import models
from utils.django.custom_models import (
    ActivityTracking,
    DirectReportPermissionAnnotateMixin,
)
from utils.global_methods.global_value_objects import UserID


@dataclass(frozen=True)
class KPIID:
    """
    This is a value object that should be used to generate and pass the KPIID to the KPIFactory
    """

    value: uuid.UUID


@dataclass(frozen=True)
class RelativeKPIID:
    """
    This is a value object that should be used to generate and pass the Relative KPIID to the Relative KPIFactory
    """

    value: uuid.UUID


# ----------------------------------------------------------------------
# KPI Model
# ----------------------------------------------------------------------


class KPI(ActivityTracking, DirectReportPermissionAnnotateMixin):
    """
    Represents KPI model
    """

    # unit types
    ABSOLUTE = "absolute"
    PERCENTAGE = "percentage"
    EURO_UNIT = "euro/unit"

    UNIT_TYPES = [
        (ABSOLUTE, "absolute"),
        (PERCENTAGE, "percentage"),
        (EURO_UNIT, "euro/unit"),
    ]

    # frequency types
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"

    FREQUENCY_TYPES = [
        (MONTHLY, "monthly"),
        (WEEKLY, "weekly"),
        (DAILY, "daily"),
        (YEARLY, "yearly"),
        (QUARTERLY, "quarterly"),
    ]

    # logic levels
    INCREASED = "increased"
    DECREASED = "decreased"

    LOGICAL_LEVEL = [
        (INCREASED, "increased"),
        (DECREASED, "decreased"),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=250, blank=False, null=False)
    reporting_person_id = models.UUIDField(blank=False, null=False)
    unit_type = models.CharField(max_length=100, choices=UNIT_TYPES, default=None)
    frequency = models.CharField(max_length=100, choices=FREQUENCY_TYPES, default=None)
    logic_level = models.CharField(max_length=100, choices=LOGICAL_LEVEL, default=None)
    unit = models.CharField(max_length=100, blank=True, null=True)
    plan_frequency = models.CharField(
        max_length=100, choices=FREQUENCY_TYPES, default=None, blank=True, null=True
    )
    user_id = models.UUIDField(blank=False, null=False)
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateTimeField(null=True, blank=True)

    def update_entity(self, data: dict):
        if data.get("name", None):
            self.name = data.get("name")
        if data.get("frequency", None):
            self.frequency = data.get("frequency")
        if data.get("plan_frequency", None):
            self.plan_frequency = data.get("plan_frequency")
        if data.get("unit", None):
            self.unit = data.get("unit")
        if data.get("logic_level", None):
            self.logic_level = data.get("logic_level")

    class Meta:
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"
        db_table = "kpi"

    def __str__(self):
        return self.name


class KPIFactory:
    @staticmethod
    def build_entity(
        id: KPIID,
        name: str,
        unit_type: str,
        frequency: str,
        logic_level: str,
        reporting_person_id: UserID,
        user_id: UserID,
        unit: str = None,
        plan_frequency: str = None,
    ) -> KPI:
        return KPI(
            id=id.value,
            name=name,
            unit_type=unit_type,
            frequency=frequency,
            logic_level=logic_level,
            unit=unit,
            reporting_person_id=reporting_person_id.value,
            plan_frequency=plan_frequency,
            user_id=user_id.value,
        )

    @classmethod
    def build_entity_with_id(
        cls,
        name: str,
        unit_type: str,
        frequency: str,
        logic_level: str,
        reporting_person_id: UserID,
        user_id: UserID,
        unit: str = None,
        plan_frequency: str = None,
    ) -> KPI:
        """This is a factory method used for build an instance of KPIs"""
        entity_id = KPIID(uuid.uuid4())
        return cls.build_entity(
            id=entity_id,
            name=name,
            unit_type=unit_type,
            frequency=frequency,
            logic_level=logic_level,
            unit=unit,
            reporting_person_id=reporting_person_id,
            plan_frequency=plan_frequency,
            user_id=user_id,
        )


# ----------------------------------------------------------------------
# Relative KPI Model
# ----------------------------------------------------------------------


class RelativeKPI(ActivityTracking):
    """
    Represents Relative KPI model
    """

    NOMINATOR = "numerator"
    DENOMINATOR = "denominator"

    KPI_LEVEL = [
        (NOMINATOR, "numerator"),
        (DENOMINATOR, "denominator"),
    ]

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    relative_kpi_id = models.UUIDField(blank=False, null=False)
    absolute_kpi_id = models.UUIDField(blank=False, null=False)
    level = models.CharField(max_length=100, choices=KPI_LEVEL, blank=False, null=False)

    class Meta:
        verbose_name = "RelativeKPI"
        verbose_name_plural = "RelativeKPIs"
        db_table = "relativekpi"

    def __str__(self):
        return f"{self.relative_kpi_id}_{self.absolute_kpi_id}"


class RelativeKPIFactory:
    @staticmethod
    def build_entity(
        id: RelativeKPIID,
        relative_kpi_id: KPIID,
        absolute_kpi_id: KPIID,
        level: str,
    ) -> RelativeKPI:
        return RelativeKPI(
            id=id.value,
            relative_kpi_id=relative_kpi_id.value,
            absolute_kpi_id=absolute_kpi_id.value,
            level=level,
        )

    @classmethod
    def build_entity_with_id(
        cls,
        relative_kpi_id: KPIID,
        absolute_kpi_id: KPIID,
        level: str,
    ) -> RelativeKPI:
        """This is a factory method used for build an instance of Relative KPIs"""
        entity_id = RelativeKPIID(uuid.uuid4())
        return cls.build_entity(
            id=entity_id,
            relative_kpi_id=relative_kpi_id,
            absolute_kpi_id=absolute_kpi_id,
            level=level,
        )
