import calendar
import importlib
import logging
from datetime import datetime, timedelta
from typing import Tuple

from django.conf import settings
from django.db import transaction
from focus_power.application.calender_manager.services import CalenderManagerAppServices
from focus_power.infrastructure.logger.models import AttributeLogger


def get_generalize_data_for_kpi():
    return dict(
        name=None,
        reporting_person_id=None,
        unit_type=None,
        frequency=None,
        logic_level=None,
        unit=None,
        kpi_frequencies=[],
        absolute_kpis=[],
        calender_manager_id=None,
        plan_frequency=None,
        year=0,
    )


def generate_dynamic_calendar(
    region: str, country: str, year: int
) -> Tuple[list, str, str]:
    module_path = f"workalendar.{region.lower()}"

    module = importlib.import_module(module_path)

    Module = getattr(module, country.capitalize())

    cal = Module()
    data = []
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    current_date = start_date
    while current_date <= end_date:
        week = current_date.isocalendar()[1]
        month = calendar.month_name[current_date.month]
        is_working_day = cal.is_working_day(current_date.date())
        is_working_day = False if current_date.weekday() == 0 else is_working_day
        is_public_holiday_day = cal.is_holiday(current_date.date())
        day_name = settings.ALL_DAYS[current_date.weekday()]
        data.append(
            {
                "name": current_date.strftime("%d/%m/%Y"),
                "week": int(week),
                "day_name": day_name,
                "day": current_date.weekday(),
                "month": month,
                "year": int(year),
                "week_name": f"{month}-CW-{int(week)}",
                "is_working_day": is_working_day,
                "is_public_holiday_day": is_public_holiday_day,
                "target": 0,
                "actual": 0,
                "is_value_updated": False,
                "system_changed_target": True,
                "system_changed_actual": True,
            }
        )
        current_date += timedelta(days=1)
    if data[0].get("week") == 52:
        del data[0]
    return data, country, region


def get_frequency_data_from_calender(year, frequency) -> dict:
    calender_manager_app_service = CalenderManagerAppServices()
    if not (
        calender_manager_app_service.calender_manager_service.get_calender_manager_repo()
        .filter(year=year)
        .first()
    ):
        calendar_data, country, region = generate_dynamic_calendar(
            country="Germany", region="Europe", year=year
        )
        with transaction.atomic():
            calender_manager = calender_manager_app_service.calender_manager_service.get_calender_manager_factory().build_entity_with_id(
                data=calendar_data,
                year=year,
                days_count=calendar_data.__len__(),
                week_count=int(calendar_data[-1].get("week")),
                country=country,
                region=region,
            )
            calender_manager.save()
    return calender_manager_app_service.generate_calender_data_from_frequency_and_year(
        year=year, frequency=frequency
    )
