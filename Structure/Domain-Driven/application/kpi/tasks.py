import logging
from datetime import date

from django.db import models
from focus_power.application.kpi.services import KPIAppServices
from focus_power.application.user.services import UserAppServices
from focus_power.celery import app
from focus_power.domain.kpi.models import KPI, RelativeKPI
from focus_power.domain.kpi.services import KPIServices, RelativeKPIServices
from focus_power.infrastructure.logger.models import AttributeLogger

from .task_services import get_frequency_data_from_calender, get_generalize_data_for_kpi


@app.task
def create_kpi_for_next_year():
    log = AttributeLogger(logging.getLogger(__name__))
    kpi_services = KPIServices()
    relative_kpi_services = RelativeKPIServices()
    kpi_app_services = KPIAppServices()
    user_app_services = UserAppServices()

    year = date.today().year + 1
    kpis = kpi_services.get_kpi_repo().all()

    for kpi in kpis:
        kpi_data = get_generalize_data_for_kpi()
        if kpi.unit_type == KPI.ABSOLUTE:
            kpi_data["name"] = kpi.name
            kpi_data["reporting_person_id"] = kpi.reporting_person_id
            kpi_data["unit_type"] = kpi.unit_type
            kpi_data["frequency"] = kpi.frequency
            kpi_data["logic_level"] = kpi.logic_level
            kpi_data["unit"] = kpi.unit
            kpi_data["plan_frequency"] = kpi.plan_frequency
            frequencies = get_frequency_data_from_calender(
                year=year, frequency=kpi_data["plan_frequency"]
            )
            kpi_data["kpi_frequencies"] = frequencies["frequency_data"]
            kpi_data["calender_manager_id"] = frequencies["calender_manager_id"]
            kpi_data["year"] = year

            creator = user_app_services.list_users().filter(id=kpi.user_id).first()

            (kpi_obj, _) = kpi_app_services.create_kpi_with_frequency_from_dict(
                data=kpi_data, user=creator
            )

            if kpi_obj:
                log.info(
                    f"KPI with name {kpi.name} and ID {kpi.id} is created with new ID {kpi_obj.id}"
                )
            else:
                log.info("Not created KPI")

        if kpi.unit_type != KPI.ABSOLUTE:
            absolute_kpis = []
            relative_kpis = (
                relative_kpi_services.get_relative_kpi_repo()
                .filter(is_active=True, relative_kpi_id=kpi.id)
                .order_by(
                    models.Case(
                        models.When(level=RelativeKPI.NOMINATOR, then=models.Value(1)),
                        models.When(
                            level=RelativeKPI.DENOMINATOR, then=models.Value(2)
                        ),
                        default=models.Value(3),
                    )
                )
            )
            for relative_kpi in relative_kpis:
                absolute_kpis.append(
                    dict(absolute_kpi_id=str(relative_kpi.id), level=relative_kpi.level)
                )

            kpi_data["name"] = kpi.name
            kpi_data["frequency"] = kpi.frequency
            kpi_data["unit_type"] = kpi.unit_type
            kpi_data["reporting_person_id"] = kpi.reporting_person_id
            kpi_data["logic_level"] = kpi.logic_level
            kpi_data["plan_frequency"] = ""
            kpi_data["absolute_kpis"] = absolute_kpis

            creator = user_app_services.list_users().filter(id=kpi.user_id).first()

            (kpi_obj, _) = kpi_app_services.create_kpi_with_frequency_from_dict(
                data=kpi_data, user=creator
            )

            if kpi_obj:
                log.info(
                    f"KPI with name {kpi.name} and ID {kpi.id} is created with new ID {kpi_obj.id}"
                )
            else:
                log.info("Not created KPI")
