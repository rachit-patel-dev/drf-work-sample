from typing import Type

from django.db.models.manager import BaseManager
from django.db.models.query import QuerySet

from .models import Forecast, ForecastFactory


class ForecastServices:
    @staticmethod
    def get_forecast_factory() -> Type[ForecastFactory]:
        return ForecastFactory

    @staticmethod
    def get_forecast_repo() -> BaseManager[Forecast]:
        return Forecast.objects

    def get_forecast_by_id(self, id: str) -> Forecast:
        return Forecast.objects.get(id=id)

    def get_forecast_by_company_id(self, company_id: str) -> QuerySet[Forecast]:
        return Forecast.objects.get(company_id=company_id)


# use of factory method
forecast_factory_method = forecast_services.get_forecast_factory()
forecast_obj = forecast_factory_method.build_entity_with_id(
    name=name,
    owner_id=UserID(value=user.id),
    forecast_data=forecast_data,
    company_id=company_id,
)
forecast_obj.save()
