from typing import Type

from django.db.models.manager import BaseManager
from utils.django.custom_models import DirectReportPermissionAnnotateMixin

from .models import KPI, KPIFactory, RelativeKPI, RelativeKPIFactory


class KPIServices:
    @staticmethod
    def get_kpi_factory() -> Type[KPIFactory]:
        return KPIFactory

    @staticmethod
    def get_kpi_repo() -> (
        DirectReportPermissionAnnotateMixin.DirectReportPermissionAnnotateManager[KPI]
    ):
        return KPI.objects

    def get_kpi_by_id(self, id: str) -> KPI:
        return KPI.objects.get(id=id)


class RelativeKPIServices:
    @staticmethod
    def get_relative_kpi_factory() -> Type[RelativeKPIFactory]:
        return RelativeKPIFactory

    @staticmethod
    def get_relative_kpi_repo() -> BaseManager[RelativeKPI]:
        return RelativeKPI.objects

    def get_relative_kpi_by_id(self, id: str) -> RelativeKPI:
        return RelativeKPI.objects.get(id=id)
