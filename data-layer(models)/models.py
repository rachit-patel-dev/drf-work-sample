"""This is a model module to store Forecast data in to the database"""

import uuid
from dataclasses import dataclass

from django.db import models
from django.utils.translation import gettext as _
from focus_power.domain.company.models import CompanyID
from utils.django import custom_models
from utils.global_methods.global_value_objects import UserID


@dataclass(frozen=True)
class ForecastID:
    """
    This is a value object that should be used to generate and pass the ForecastID to the ForecastFactory
    """

    value: uuid.UUID


# ----------------------------------------------------------------------
# Forecast Model
# ----------------------------------------------------------------------


class Forecast(custom_models.ActivityTracking):
    """
    Represents Forecast model
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=250, null=True, blank=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    responsible_person_id = models.UUIDField(blank=True, null=True)
    owner_id = models.UUIDField(blank=False, null=False)
    rolling_period = models.IntegerField(default=0)
    forecast_data = models.JSONField(blank=False, null=False)
    company_id = models.UUIDField(blank=False, null=False)

    class Meta:
        verbose_name = "Forecast"
        verbose_name_plural = "Forecasts"
        db_table = "forecast"


class ForecastFactory:
    @staticmethod
    def build_entity(
        id: ForecastID,
        name: str,
        company_id: CompanyID,
        owner_id: UserID,
        forecast_data: dict,
    ) -> Forecast:
        return Forecast(
            id=id.value,
            name=name,
            owner_id=owner_id,
            forecast_data=forecast_data,
            company_id=company_id,
        )

    @classmethod
    def build_entity_with_id(
        cls,
        name: str,
        owner_id: UserID,
        forecast_data: dict,
        company_id: CompanyID,
    ) -> Forecast:
        """This is a factory method used for build an instance of Forecast"""
        entity_id = ForecastID(uuid.uuid4())
        return cls.build_entity(
            id=entity_id,
            name=name,
            owner_id=owner_id.value,
            forecast_data=forecast_data,
            company_id=company_id,
        )
