import datetime
from datetime import timezone
from typing import List, Tuple, Union

from django.conf import settings
from django.db import models, transaction
from django.db.models import CharField, OuterRef, Subquery, Value
from django.db.models.query import QuerySet
from focus_power.application.base.baseAppService import (
    BaseAppServiceWithAttributeLogger,
)
from focus_power.application.calender_manager.services import CalenderManagerAppServices
from focus_power.application.company.services import CompanyDivisionAppServices
from focus_power.application.direct_report.services import DirectReportAppServices
from focus_power.application.division.services import UserDivisionAppServices
from focus_power.application.reportee_tracker.services import ReporteeTrackerAppServices
from focus_power.application.roles.services import UserRolesAppServices
from focus_power.application.user.services import UserAppServices
from focus_power.domain.calender_manager.models import (
    CalenderManager,
    CalenderManagerID,
)
from focus_power.domain.kpi.kpi_frequency.models import KPIFrequency
from focus_power.domain.kpi.kpi_frequency.services import KPIFrequencyServices
from focus_power.domain.kpi.models import KPI, KPIID, RelativeKPI
from focus_power.domain.kpi.services import KPIServices, RelativeKPIServices
from focus_power.domain.user.models import User
from focus_power.infrastructure.logger.models import AttributeLogger
from utils.django.dto.general_dto import KPIWithFrequencyDto
from utils.django.exceptions import (
    AbsoluteKPIsNotAllowedException,
    AbsoluteKPIsNotFoundException,
    AbsoluteKPIsNotProvidedException,
    KPIFrequencyDataNotValidatedException,
    KPIFrequencyException,
    KPIFrequencyNotFoundException,
    KPIFrequencyNotProvidedException,
    KPINotExistsException,
    KPIsException,
    KPIsUnitNotProvidedException,
    NotFromSameCompanyException,
    NotPercentageKPIException,
    RelativeKPINotFoundException,
    ResponsiblePersonNotFoundException,
)
from utils.global_methods.global_value_objects import UserID
from utils.global_methods.instance_permissions_generator import (
    generate_instance_permissions,
    generate_permissions_for_all_seniors,
)


class KPIAppServices(BaseAppServiceWithAttributeLogger):

    def __init__(self) -> None:
        self.kpi_services = KPIServices()
        self.kpi_frequency_service = KPIFrequencyServices()
        self.relative_kpi_services = RelativeKPIServices()
        self.user_app_service = UserAppServices()
        self.user_roles_app_service = UserRolesAppServices()
        self.user_roles_app_service = UserRolesAppServices()
        self.calender_manager_app_service = CalenderManagerAppServices()
        self.relative_kpi_app_service = RelativeKPIAppServices()
        self.user_division_app_service = UserDivisionAppServices()
        self.company_division_app_services = CompanyDivisionAppServices()
        self.reportee_tracker_app_service = ReporteeTrackerAppServices()
        self.direct_report_app_service = DirectReportAppServices()

    def list_owner_kpi(self, user: User) -> QuerySet[KPI]:
        """This method will return all the owner's KPI"""
        return self.kpi_services.get_kpi_repo().filter(
            reporting_person_id=user.id, is_active=True, is_archived=False
        )

    def list_reportee_kpi_count(self, user_id) -> QuerySet[KPI]:
        """This method will return total count of KPI for reporting person"""
        return (
            self.kpi_services.get_kpi_repo()
            .filter(reporting_person_id=user_id, is_active=True, is_archived=False)
            .count()
        )

    def update_queryset_by_params(
        self,
        queryset: Union[QuerySet[KPI], QuerySet[KPIFrequency]],
        update_params: dict = {},
    ):
        queryset.update(**update_params)

    def list_kpi(
        self,
        user: User,
        direct_report_id: str,
        serializer_context: dict = {},
        company_id=None,
    ) -> Tuple[QuerySet[KPI], dict]:
        """This method will return list of KPIs."""
        direct_report = self.direct_report_app_service.get_direct_report_by_id(
            direct_report_id=direct_report_id
        )
        permissions_dict = {
            item["id"]: item["permissions"] for item in direct_report.kpis
        }
        if company_id:
            ceo_user_object = self.user_app_service.get_ceo_user_object(
                company_id=company_id
            )
            user = ceo_user_object if ceo_user_object else user

        # reporting person list
        reporting_person_id_list = (
            self.list_all_kpi(user=user, company_id=company_id)
            .filter(id__in=list(permissions_dict.keys()))
            .values_list("reporting_person_id", flat=True)
        )
        reporting_person_list = list(
            self.user_app_service.list_users()
            .filter(id__in=reporting_person_id_list)
            .values("id", "first_name", "last_name", "profile_image")
        )
        reporting_person_dict = {user.get("id"): user for user in reporting_person_list}
        serializer_context.update({"reporting_person_dict": reporting_person_dict})

        kpi_query_set = (
            self.kpi_services.get_kpi_repo()
            .annotate_by_direct_report_permission(
                permissions=direct_report.kpis,
                filters=dict(
                    is_active=True,
                    is_archived=False,
                    id__in=list(permissions_dict.keys()),
                ),
            )
            .order_by("-created_at")
        )

        return kpi_query_set, serializer_context

    def list_all_kpi(self, user: User, company_id=None) -> QuerySet[KPI]:
        """This method will return list of KPIs."""
        user_role = self.user_roles_app_service.get_user_role_by_user_id(
            user_id=user.id
        )

        users_list = (
            self.user_roles_app_service.list_user_roles()
            .filter(
                company_id=(
                    company_id
                    if (company_id and user_role.is_success_manager)
                    else user_role.company_id
                )
            )
            .values_list("user_id", flat=True)
        )

        return (
            self.kpi_services.get_kpi_repo()
            .filter(
                is_active=True, reporting_person_id__in=users_list, is_archived=False
            )
            .order_by("-created_at")
        )

    def list_absolute_kpis(self, user: User, company_id=None) -> QuerySet[KPI]:
        """This method will return list of Absolute KPIs."""
        return self.list_all_kpi(user=user, company_id=company_id).filter(
            unit_type=KPI.ABSOLUTE
        )

    def create_kpi_with_frequency_from_dict(
        self, data: dict, user: User, company_id=None
    ) -> Tuple[KPI, bool]:
        name = data.get("name")
        reporting_person_id = data.get("reporting_person_id")
        unit_type = data.get("unit_type")
        frequency = data.get("frequency")
        logic_level = data.get("logic_level")
        unit = data.get("unit")
        absolute_kpis = data.get("absolute_kpis", [])
        kpi_frequencies = data.get("kpi_frequencies")
        plan_frequency = data.get("plan_frequency")
        calender_manager_id = data.get("calender_manager_id")
        year = data.get("year")
        if not (
            (unit_type == KPI.ABSOLUTE and unit)
            or (unit_type != KPI.ABSOLUTE and not unit)
        ):
            raise KPIsUnitNotProvidedException(
                "kpi-unit-not-provided-exception",
                "kpi unit is not provided",
                self.log,
            )

        if (unit_type != KPI.ABSOLUTE) and (len(absolute_kpis) == 0):
            raise AbsoluteKPIsNotProvidedException(
                "absolute-kpi-not-provided-exception",
                "Absolute kpis are not provided",
                self.log,
            )

        if company_id:
            ceo_user_object = self.user_app_service.get_ceo_user_object(
                company_id=company_id
            )
            user = ceo_user_object if ceo_user_object else user

        absolute_kpis_queryset = self.list_all_kpi(
            user=user, company_id=company_id
        ).filter(id__in=[kpi.get("absolute_kpi_id") for kpi in absolute_kpis])
        if unit_type == KPI.ABSOLUTE and absolute_kpis_queryset.count() > 0:
            raise AbsoluteKPIsNotAllowedException(
                "absolute-kpi-not-found", "absolute kpi not allowed", self.log
            )
        elif unit_type != KPI.ABSOLUTE and not (absolute_kpis_queryset.count() == 2):
            raise AbsoluteKPIsNotAllowedException(
                "absolute-kpi-not-found", "absolute kpi not allowed", self.log
            )
        responsible_person_user = self.user_app_service.list_users().filter(
            id=reporting_person_id
        )
        if not responsible_person_user:
            error_message = "Responsible person does not exist"
            raise ResponsiblePersonNotFoundException(
                "responsible-person-exception", error_message, self.log
            )

        responsible_person_user = responsible_person_user.first()

        if not self.user_roles_app_service.is_users_from_same_company(
            users=[user, responsible_person_user]
        ):
            error_message = "Responsible person does not belongs to same user company."
            raise NotFromSameCompanyException(
                "company-exception", error_message, self.log
            )
        try:
            with transaction.atomic():
                kpi_factory_method = self.kpi_services.get_kpi_factory()
                kpi_obj = kpi_factory_method.build_entity_with_id(
                    name=name,
                    unit_type=unit_type,
                    unit=unit,
                    frequency=frequency,
                    logic_level=logic_level,
                    reporting_person_id=UserID(value=responsible_person_user.id),
                    plan_frequency=plan_frequency,
                    user_id=UserID(value=user.id),
                )
                kpi_obj.save()

                # update direct report
                #  Conditions for reporting persons permission
                kpi_instance = generate_instance_permissions(instance_id=kpi_obj.id)
                self.direct_report_app_service.update_direct_report_by_user_id(
                    user=responsible_person_user,
                    module_type="kpis",
                    instance=kpi_instance,
                )

                # updated condition: Give access to all_seniors for read and write
                all_seniors = self.reportee_tracker_app_service.get_all_seniors(
                    reportee_id=str(responsible_person_user.id)
                )

                if all_seniors:
                    generate_permissions_for_all_seniors(
                        log=self.log,
                        user=responsible_person_user,
                        instance_id=kpi_obj.id,
                        module_type="kpis",
                        seniors_list=all_seniors,
                    )

                # add absolute kpis if type is Euro/unit or percentage
                if unit_type != KPI.ABSOLUTE:
                    relative_kpi_factory = (
                        self.relative_kpi_services.get_relative_kpi_factory()
                    )
                    for absolute_kpi in absolute_kpis:
                        relative_kpi_obj = relative_kpi_factory.build_entity_with_id(
                            relative_kpi_id=KPIID(value=kpi_obj.id),
                            absolute_kpi_id=KPIID(
                                value=absolute_kpi.get("absolute_kpi_id")
                            ),
                            level=absolute_kpi.get("level"),
                        )
                        relative_kpi_obj.save()
                    return kpi_obj, unit_type == KPI.ABSOLUTE
                # create kpi frequencies
                if not kpi_frequencies:
                    raise KPIFrequencyNotProvidedException(
                        "kpi-frequency-exception",
                        "kpi frequency data not provided",
                        self.log,
                    )
                initial_data = {
                    frequency_type[0]: [] for frequency_type in KPI.FREQUENCY_TYPES
                }
                initial_data[plan_frequency] = kpi_frequencies
                (
                    validated,
                    converted_data,
                ) = self.calender_manager_app_service.convert_data_with_target_values(
                    plan_frequency=plan_frequency,
                    year=year,
                    is_new_data=True,
                    initial_data=initial_data,
                    value_type="target",
                )
                if not validated:
                    raise KPIFrequencyDataNotValidatedException(
                        "kpi-frequency-data-validation-exception",
                        "kpi frequency data is not validated",
                        self.log,
                    )
                kpi_frequency_factory = (
                    self.kpi_frequency_service.get_kpi_frequency_factory()
                )
                kpi_frequency_obj = kpi_frequency_factory.build_entity_with_id(
                    kpi_id=KPIID(value=kpi_obj.id),
                    calender_manager_id=CalenderManagerID(value=calender_manager_id),
                    frequency=frequency,
                    daily_data=converted_data[KPI.DAILY],
                    weekly_data=converted_data[KPI.WEEKLY],
                    monthly_data=converted_data[KPI.MONTHLY],
                    quarterly_data=converted_data[KPI.QUARTERLY],
                    yearly_data=converted_data[KPI.YEARLY],
                )
                kpi_frequency_obj.save()
                return kpi_obj, unit_type == KPI.ABSOLUTE
        except Exception as e:
            if isinstance(e, Exception):
                raise KPIsException("KPI-exception", str(e), self.log)
            else:
                raise e

    def update_kpi_frequency_values(
        self,
        data: dict,
        kpi_id: str,
        user: User,
        value_type: str,
        filter_frequency: str = None,
        company_id=None,
    ) -> bool:
        kpi_queryset = self.list_all_kpi(user=user, company_id=company_id).filter(
            id=kpi_id
        )
        if not kpi_queryset:
            raise AbsoluteKPIsNotFoundException(
                "absolute-kpi-not-found-exception",
                "This Absolute KPI not found",
                self.log,
            )
        kpi_queryset = kpi_queryset.first()
        reporting_frequency = (
            kpi_queryset.frequency if not filter_frequency else filter_frequency
        )
        plan_frequency = kpi_queryset.plan_frequency
        kpi_frequency_queryset = (
            self.kpi_frequency_service.get_kpi_frequency_repo().filter(
                kpi_id=kpi_queryset.id, is_archived=False, is_active=True
            )
        )
        if not kpi_frequency_queryset:
            raise KPIFrequencyNotFoundException(
                "kpi-frequency-not-found-exception",
                "KPI frequency for this absolute kpi not found.",
                self.log,
            )
        kpi_frequencies = data.get("kpi_frequencies")
        kpi_frequency_data = kpi_frequency_queryset[0]
        year = kpi_frequency_data.yearly_data[0].get("name")
        initial_data = {frequency[0]: None for frequency in KPI.FREQUENCY_TYPES}
        for frequency_type in KPI.FREQUENCY_TYPES:
            initial_data[frequency_type[0]] = getattr(
                kpi_frequency_data, f"{frequency_type[0]}_data"
            )
        initial_data[reporting_frequency] = kpi_frequencies
        (
            validated,
            converted_data,
        ) = self.calender_manager_app_service.convert_data_with_target_values(
            reporting_frequency=reporting_frequency,
            plan_frequency=plan_frequency,
            year=year,
            is_new_data=False,
            initial_data=initial_data,
            value_type=value_type,
        )
        if not validated:
            raise KPIFrequencyDataNotValidatedException(
                "kpi-frequency-data-exception",
                "KPI frequency data is not validated",
                self.log,
            )
        try:
            with transaction.atomic():
                kpi_frequency_data.daily_data = converted_data[KPI.DAILY]
                kpi_frequency_data.weekly_data = converted_data[KPI.WEEKLY]
                kpi_frequency_data.monthly_data = converted_data[KPI.MONTHLY]
                kpi_frequency_data.yearly_data = converted_data[KPI.YEARLY]
                kpi_frequency_data.quarterly_data = converted_data[KPI.QUARTERLY]
                kpi_frequency_data.save()
                return True
        except Exception as e:
            raise KPIFrequencyException(
                "KPI-frequency-exception",
                "An error occurred while updating the values of frequency-data.",
                self.log,
            )

    def __get_current_week(self, date):
        week = date.isocalendar()[1]
        quarter = (date.month - 1) // 3 + 1
        return f"{date.year} - Q{quarter} - CW {week}"

    def get_last_date(self, query_params: dict):
        year = int(query_params.get("year", datetime.datetime.now().year))
        month = int(query_params.get("month", datetime.datetime.now().month))
        today = datetime.date.today()
        current_week = self.__get_current_week(today)
        # Check if the current date matches the given year and month
        if today.year == year and today.month == month:
            return year, month, today, current_week
        # If not, find the last date of the given year and month
        last_date = datetime.date(year, month, 1) + datetime.timedelta(days=31)
        last_date = last_date.replace(day=1) - datetime.timedelta(days=1)
        return year, month, last_date, current_week

    def update_reporting_person(
        self, pk, data: dict, user: User, serializer_context: dict = {}, company_id=None
    ) -> Tuple[QuerySet[KPI], dict]:
        reporting_person_id = data.get("reporting_person", None)
        exists_kpi = self.list_all_kpi(user=user, company_id=company_id).filter(id=pk)
        if not exists_kpi:
            raise KPINotExistsException(
                "kpi-not-exists", "KPI with this id doesn't exists", self.log
            )
        reporting_person_user = self.user_app_service.list_users().filter(
            id=reporting_person_id
        )
        if not reporting_person_user:
            raise ResponsiblePersonNotFoundException(
                "reporting-person-exception",
                "Reporting person does not exists",
                self.log,
            )
        try:
            reporting_person_user = reporting_person_user.first()
            with transaction.atomic():
                kpi_obj = exists_kpi.first()

                # removing the instance from the direct reports of old reporting person's hierarchy
                old_reporting_person = (
                    self.user_app_service.list_users()
                    .filter(id=kpi_obj.reporting_person_id)
                    .first()
                )
                self.direct_report_app_service.remove_instance_from_direct_report(
                    user=old_reporting_person,
                    module_type="kpis",
                    instance=str(kpi_obj.id),
                )

                # assigning the new reporting person
                kpi_obj.reporting_person_id = reporting_person_user.id
                kpi_obj.save()

                # updating the direct report
                kpi_instance = generate_instance_permissions(instance_id=kpi_obj.id)
                self.direct_report_app_service.update_direct_report_by_user_id(
                    user=reporting_person_user,
                    module_type="kpis",
                    instance=kpi_instance,
                )

                all_seniors = self.reportee_tracker_app_service.get_all_seniors(
                    reportee_id=str(reporting_person_user.id)
                )
                # updated condition: Give access to all_seniors
                if all_seniors:
                    generate_permissions_for_all_seniors(
                        log=self.log,
                        user=reporting_person_user,
                        instance_id=kpi_obj.id,
                        module_type="kpis",
                        seniors_list=all_seniors,
                    )

                # reporting person list
                reporting_person_list = list(
                    self.user_app_service.list_users()
                    .filter(id=kpi_obj.reporting_person_id)
                    .values("id", "first_name", "last_name", "profile_image")
                )
                reporting_person_dict = {
                    user.get("id"): user for user in reporting_person_list
                }
                serializer_context.update(
                    {"reporting_person_dict": reporting_person_dict}
                )

                return kpi_obj, serializer_context
        except Exception as e:
            raise KPIsException(
                "kpi-reporting-person-update-exception", str(e), self.log
            )

    def update_numerator_denominator_from_dict(
        self, existing_kpi, data: dict, user: User, company_id=None
    ) -> KPI:
        numerator = data.get("numerator")
        denominator = data.get("denominator")
        kpi_queryset = self.list_all_kpi(user=user, company_id=company_id)
        numerator_obj = kpi_queryset.filter(id=numerator).first()
        denominator_obj = kpi_queryset.filter(id=denominator).first()
        if not (existing_kpi and numerator_obj and denominator_obj):
            raise KPINotExistsException(
                "kpi-not-exists", "KPI with this id doesn't exists", self.log
            )
        try:
            with transaction.atomic():
                self.relative_kpi_app_service.update_relative_kpi(
                    kpi=existing_kpi,
                    numerator_obj=numerator_obj,
                    denominator_obj=denominator_obj,
                    user=user,
                )
                return existing_kpi
        except Exception as e:
            raise e

    def update_kpi_from_dict(
        self,
        kpi_id,
        data: dict,
        user: User,
        serializer_context: dict = {},
        company_id=None,
    ) -> Tuple[QuerySet[KPI], dict]:
        exists_kpi = self.list_all_kpi(user=user, company_id=company_id).filter(
            id=kpi_id
        )
        absolute_kpis = data.get("absolute_kpis", None)
        if not exists_kpi:
            raise KPINotExistsException(
                "kpi-not-exists-exception", "KPI does not exists", self.log
            )
        exists_kpi = exists_kpi.first()
        if exists_kpi.unit_type == KPI.ABSOLUTE:
            plan_frequency = data.get("plan_frequency", None)
            if plan_frequency:
                kpi_frequencies = data.get("kpi_frequencies", None)
                if not kpi_frequencies:
                    raise KPIFrequencyNotFoundException(
                        "kpi-frequency-exception",
                        "You have to provide KPI frequency data",
                        self.log,
                    )
        try:
            with transaction.atomic():
                kpi_obj = exists_kpi
                kpi_obj.update_entity(data=data)
                kpi_obj.save()
                if data.get("kpi_frequencies"):
                    self.update_kpi_frequency_values(
                        data=data,
                        kpi_id=kpi_id,
                        user=user,
                        filter_frequency=data.get("plan_frequency", None),
                        value_type=data.get("value_type"),
                        company_id=company_id,
                    )
                if exists_kpi.unit_type != KPI.ABSOLUTE:
                    if absolute_kpis:
                        self.update_numerator_denominator_from_dict(
                            data=absolute_kpis,
                            user=user,
                            existing_kpi=exists_kpi,
                            company_id=company_id,
                        )

                # reporting person list
                reporting_person_list = list(
                    self.user_app_service.list_users()
                    .filter(id=kpi_obj.reporting_person_id)
                    .values("id", "first_name", "last_name", "profile_image")
                )
                reporting_person_dict = {
                    user.get("id"): user for user in reporting_person_list
                }
                serializer_context.update(
                    {"reporting_person_dict": reporting_person_dict}
                )
                return kpi_obj, serializer_context
        except Exception as e:
            raise e

    def get_kpi_by_id(
        self, kpi_id, user: User, serializer_context: dict = {}, company_id=None
    ) -> Tuple[QuerySet[KPI], dict]:
        try:
            kpi_obj = self.list_all_kpi(user=user, company_id=company_id).get(id=kpi_id)

            # reporting person list
            reporting_person_list = list(
                self.user_app_service.list_users()
                .filter(id=kpi_obj.reporting_person_id)
                .values("id", "first_name", "last_name", "profile_image")
            )
            reporting_person_dict = {
                user.get("id"): user for user in reporting_person_list
            }
            serializer_context.update({"reporting_person_dict": reporting_person_dict})

            return kpi_obj, serializer_context
        except Exception as e:
            raise KPIsException("kpi-not-found", "KPI does not found", self.log)

    def get_kpi_by_kpi_id(self, kpi_id) -> KPI:
        try:
            return self.kpi_services.get_kpi_by_id(kpi_id)
        except Exception as e:
            raise KPIsException("kpi-not-found", "KPI does not found", self.log)

    def list_kpi_by_user_id(self, user_id, kpi_id_list) -> QuerySet[KPI]:
        """This method will return list of KPIs by user."""
        return self.kpi_services.get_kpi_repo().filter(
            is_active=True,
            reporting_person_id=user_id,
            id__in=kpi_id_list,
            is_archived=False,
        )

    def get_kpi_with_frequency_by_kpi_list(
        self, kpi_ids: list, filter_params: dict = {}
    ) -> KPIWithFrequencyDto:
        kpi_queryset = self.kpi_services.get_kpi_repo().filter(
            id__in=kpi_ids, is_active=True, **filter_params
        )
        kpi_frequency_queryset = (
            self.kpi_frequency_service.get_kpi_frequency_repo().filter(
                kpi_id__in=kpi_ids, is_active=True, **filter_params
            )
        )
        if not (kpi_queryset and kpi_frequency_queryset):
            raise KPINotExistsException(
                "kpi-not-exists-exception",
                "KPI and frequency does not exists",
                self.log,
            )
        return KPIWithFrequencyDto(
            kpis=kpi_queryset, kpi_frequencies=kpi_frequency_queryset
        )

    def delete_kpi(self, kpi_id: str, user: User) -> bool:
        """This method will delete the kpi by user role"""
        try:
            with transaction.atomic():
                kpi_data = self.get_kpi_with_frequency_by_kpi_list(kpi_ids=[kpi_id])
                data = self.user_app_service.get_user_role_ceo_or_c_level_with_extended_user(
                    user=user
                )
                if data.is_ceo:
                    # Soft deleting the kpi and kpi frequency if ceo
                    self.update_queryset_by_params(
                        queryset=kpi_data.kpis,
                        update_params=dict(is_active=False),
                    )
                    self.update_queryset_by_params(
                        queryset=kpi_data.kpi_frequencies,
                        update_params=dict(is_active=False),
                    )
                elif data.is_c_level:
                    # Soft deleting the kpi and kpi frequency if c level
                    direct_report_for_login_user = (
                        self.direct_report_app_service.get_direct_report_by_user_id(
                            user_id=user.id
                        )
                    )
                    # mapping the permission data by it's instance's w==True
                    kpi_data_by_permission = list(
                        map(
                            lambda instance: instance["id"],
                            filter(
                                lambda instance: instance["permissions"].get("w", False)
                                == True,
                                direct_report_for_login_user.kpis,
                            ),
                        )
                    )
                    if kpi_id in kpi_data_by_permission:
                        # Soft deleting the kpi and kpi frequency if ceo

                        self.update_queryset_by_params(
                            queryset=kpi_data.kpis,
                            update_params=dict(is_active=False),
                        )
                        self.update_queryset_by_params(
                            queryset=kpi_data.kpi_frequencies,
                            update_params=dict(is_active=False),
                        )
                return True
        except Exception as e:
            raise e

    def archive_kpi(self, kpi_list: list, user: User, archive: bool = True) -> bool:
        try:
            with transaction.atomic():
                kpi_data = self.get_kpi_with_frequency_by_kpi_list(
                    kpi_ids=kpi_list, filter_params=dict(is_archived=not archive)
                )
                data = self.user_app_service.get_user_role_ceo_or_c_level_with_extended_user(
                    user=user
                )
                if data.is_ceo:
                    # archive the kpi and kpi frequency if ceo
                    self.update_queryset_by_params(
                        queryset=kpi_data.kpis,
                        update_params=dict(
                            is_archived=archive,
                            archived_date=datetime.datetime.now(tz=timezone.utc),
                        ),
                    )
                    self.update_queryset_by_params(
                        queryset=kpi_data.kpi_frequencies,
                        update_params=dict(is_archived=archive),
                    )
                elif data.is_c_level:
                    # Soft deleting the kpi and kpi frequency if c level
                    direct_report_for_login_user = (
                        self.direct_report_app_service.get_direct_report_by_user_id(
                            user_id=user.id
                        )
                    )
                    # mapping the permission data by it's instance's w==True
                    kpi_data_by_permission = list(
                        map(
                            lambda instance: instance["id"],
                            filter(
                                lambda instance: instance["permissions"].get("w", False)
                                == True,
                                direct_report_for_login_user.kpis,
                            ),
                        )
                    )
                    if all(element in kpi_list for element in kpi_data_by_permission):
                        # archive the kpi and kpi frequency if ceo
                        self.update_queryset_by_params(
                            queryset=kpi_data.kpis,
                            update_params=dict(
                                is_archive=archive,
                                archived_date=datetime.datetime.now(tz=timezone.utc),
                            ),
                        )
                        self.update_queryset_by_params(
                            queryset=kpi_data.kpi_frequencies,
                            update_params=dict(is_archive=archive),
                        )
                return True
        except Exception as e:
            raise e


class KPIFrequencyAppServices(BaseAppServiceWithAttributeLogger):
    def __init__(
        self,
        user: User,
        context: dict = {},
        kpi_obj: Union[KPI, None] = None,
    ) -> None:
        self.user = user
        self.kpi_services = KPIServices()
        self.kpi_app_services = KPIAppServices()
        self.kpi_frequency_services = KPIFrequencyServices()
        self.user_app_service = UserAppServices()
        self.calender_manager_app_service = CalenderManagerAppServices()
        self.related_kpi_app_service = RelativeKPIAppServices()
        self.context = context
        self.target_month = None
        self.target_date = None
        self.kpi_obj = kpi_obj
        self.related_kpi_frequencies = self.get_related_kpi_frequencies()

    def list_all_kpi_frequency(self, user: User) -> QuerySet[KPIFrequency]:
        """This method will return list of KPI-Frequency."""
        return self.kpi_frequency_services.get_kpi_frequency_repo().filter(
            is_active=True, is_archived=False
        )

    def get_related_kpi_frequencies(self):
        if isinstance(self.kpi_obj, KPI) and self.kpi_obj.unit_type != KPI.ABSOLUTE:
            related_kpis = self.related_kpi_app_service.list_relative_absolute_kpis(
                kpi_id=self.kpi_obj.id, user=self.user
            ).values_list("id")
            related_kpis = [str(related_kpi[0]) for related_kpi in related_kpis]
            return (
                self.list_all_kpi_frequency(user=self.user)
                .filter(kpi_id__in=related_kpis)
                .order_by(
                    models.Case(
                        *[
                            models.When(kpi_id=pk, then=pos)
                            for pos, pk in enumerate(related_kpis)
                        ]
                    )
                )
            )

    def get_kpi_frequency_data_by_kpi_id(
        self,
        kpi_id: str,
        user: User,
        filter_frequency: str = None,
        is_cumulative: bool = False,
        is_percentage: bool = False,
        for_graph: bool = False,
        for_bar: bool = False,
        start_date=None,
        end_date=None,
        company_id=None,
    ) -> List[dict]:
        kpi_queryset = self.kpi_app_services.list_all_kpi(
            user=user, company_id=company_id
        ).filter(id=kpi_id)
        if not kpi_queryset:
            raise AbsoluteKPIsNotFoundException(
                "absolute-kpi-not-found-exception",
                "This Absolute KPI not found",
                self.log,
            )
        kpi_queryset = kpi_queryset.first()
        if is_percentage:
            if not (
                kpi_queryset.unit_type == KPI.PERCENTAGE
                or kpi_queryset.unit_type == KPI.EURO_UNIT
            ):
                raise NotPercentageKPIException(
                    "not-percentage-kpi-exception",
                    "This KPI is not percentage KPI.",
                    self.log,
                )
            related_kpis = self.related_kpi_app_service.list_relative_absolute_kpis(
                kpi_id=kpi_id, user=user
            ).values_list("id")
            related_kpis = [str(related_kpi[0]) for related_kpi in related_kpis]
            kpi_frequencies = (
                self.list_all_kpi_frequency(user=self.user)
                .filter(kpi_id__in=related_kpis)
                .order_by(
                    models.Case(
                        *[
                            models.When(kpi_id=pk, then=pos)
                            for pos, pk in enumerate(related_kpis)
                        ]
                    )
                )
            )
            percentage_data = (
                self.calender_manager_app_service.get_nominator_by_denominator_data(
                    nominator_data=getattr(
                        kpi_frequencies[0], f"{filter_frequency}_data"
                    ),
                    denominator_data=getattr(
                        kpi_frequencies[1], f"{filter_frequency}_data"
                    ),
                    type=kpi_queryset.unit_type,
                )
            )
            percentage_data = (
                percentage_data
                if not is_cumulative
                else self.calender_manager_app_service.calculate_cumulative_data(
                    data=percentage_data
                )
            )
            if for_graph:
                percentage_data = (
                    self.calender_manager_app_service.graph_formate_convertor(
                        input_data=percentage_data,
                        frequency=filter_frequency,
                        start_date=start_date,
                        end_date=end_date,
                        for_bar=for_bar,
                    )
                )
            return percentage_data
        frequency = kpi_queryset.frequency if not filter_frequency else filter_frequency
        kpi_frequency_queryset = (
            self.kpi_frequency_services.get_kpi_frequency_repo().filter(
                kpi_id=kpi_queryset.id, is_active=True, is_archived=False
            )
        )
        if not kpi_frequency_queryset:
            raise KPIFrequencyNotFoundException(
                "kpi-frequency-not-found-exception",
                "KPI frequency for this absolute kpi not found.",
                self.log,
            )
        frequency_data = getattr(kpi_frequency_queryset.first(), f"{frequency}_data")
        validated = self.calender_manager_app_service.validate_data(
            data=frequency_data, frequency=frequency
        )
        if not validated:
            raise KPIFrequencyDataNotValidatedException(
                "kpi-frequency-data-exception",
                "KPI frequency data is not validated",
                self.log,
            )
        frequency_data = (
            frequency_data
            if not is_cumulative
            else self.calender_manager_app_service.calculate_cumulative_data(
                data=frequency_data
            )
        )
        if for_graph:
            frequency_data = self.calender_manager_app_service.graph_formate_convertor(
                input_data=frequency_data,
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                for_bar=for_bar,
            )
        return frequency_data

    def count_target_actual_until_date(
        self, data, target_month, target_date, for_month=True
    ):
        target_count = 0
        actual_count = 0
        for entry in data:
            month_name = entry["month"]
            entry_date = datetime.datetime.strptime(entry["name"], "%d/%m/%Y").date()
            if for_month:
                if month_name == target_month and entry_date <= target_date:
                    target_count += entry["target"]
                    actual_count += entry["actual"]
            else:
                target_count += entry["target"]
                actual_count += entry["actual"]
                if entry_date == target_date:
                    break
        return target_count, actual_count

    def count_target_actual_for_related_kpi(
        self,
        related_kpi_frequencies: QuerySet[KPIFrequency],
        target_month,
        target_date,
        for_month=True,
        is_percentage=False,
    ):
        target_count_list = []
        actual_count_list = []
        for kpi_frequency in related_kpi_frequencies:
            target_count, actual_count = self.count_target_actual_until_date(
                data=kpi_frequency.daily_data,
                target_month=target_month,
                target_date=target_date,
                for_month=for_month,
            )
            target_count_list.append(float(target_count))
            actual_count_list.append(float(actual_count))
        if not is_percentage:
            return (
                (
                    target_count_list[0] / target_count_list[1]
                    if target_count_list[1] != 0
                    else 0
                ),
                (
                    actual_count_list[0] / actual_count_list[1]
                    if actual_count_list[1] != 0
                    else 0
                ),
            )
        else:
            return (
                (target_count_list[0] / target_count_list[1]) * 100
                if target_count_list[1] != 0
                else 0
            ), (
                (actual_count_list[0] / actual_count_list[1]) * 100
                if actual_count_list[1] != 0
                else 0
            )

    def set_target_month_and_target_date(self) -> None:
        self.target_month = settings.ALL_MONTHS[self.context.get("month") - 1]
        self.target_date = self.context.get("last_date")

    def get_percentage(
        self, base_value: Union[float, int], actual_value: Union[float, int]
    ) -> Union[float, int]:
        if base_value <= 0:
            return 0
        return (float(actual_value) * float(100)) / float(base_value)

    def calculate_total_calculation_data_of_kpis(self, calculation_data: dict) -> None:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpis = self.related_kpi_app_service.list_relative_absolute_kpis(
            kpi_id=self.kpi_obj.id, user=self.user
        ).values_list("id")
        related_kpi_frequencies = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id__in=related_kpis
        )
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                data=kpi_frequency[0].daily_data,
                target_month=self.target_month,
                target_date=self.target_date,
            )

    def calculate_total_monthly_target(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpi_frequencies = self.get_related_kpi_frequencies()
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                data=kpi_frequency[0].daily_data,
                target_month=self.target_month,
                target_date=self.target_date,
            )
            return target_count
        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=True,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return target_count

    def calculate_total_monthly_actual(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpi_frequencies = self.get_related_kpi_frequencies()
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                kpi_frequency[0].daily_data, self.target_month, self.target_date
            )
            return actual_count
        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=True,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return actual_count

    def calculate_total_monthly_percentage(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpi_frequencies = self.get_related_kpi_frequencies()
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                kpi_frequency[0].daily_data, self.target_month, self.target_date
            )
            return self.get_percentage(
                base_value=target_count, actual_value=actual_count
            )
        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=True,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return self.get_percentage(base_value=target_count, actual_value=actual_count)

    def calculate_total_ytd_target(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpi_frequencies = self.get_related_kpi_frequencies()
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                kpi_frequency[0].daily_data, self.target_month, self.target_date, False
            )
            return target_count
        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=False,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return target_count

    def calculate_total_ytd_actual(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpis = self.related_kpi_app_service.list_relative_absolute_kpis(
            kpi_id=self.kpi_obj.id, user=self.user
        ).values_list("id")
        related_kpi_frequencies = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id__in=related_kpis
        )
        related_kpis = [str(related_kpi[0]) for related_kpi in related_kpis]
        related_kpi_frequencies = (
            self.list_all_kpi_frequency(user=self.user)
            .filter(kpi_id__in=related_kpis)
            .order_by(
                models.Case(
                    *[
                        models.When(kpi_id=pk, then=pos)
                        for pos, pk in enumerate(related_kpis)
                    ]
                )
            )
        )
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                kpi_frequency[0].daily_data, self.target_month, self.target_date, False
            )
            return actual_count
        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=False,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return actual_count

    def calculate_total_ytd_percentage(self) -> int:
        kpi_frequency = self.list_all_kpi_frequency(user=self.user).filter(
            kpi_id=self.kpi_obj.id
        )
        related_kpi_frequencies = self.get_related_kpi_frequencies()
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date(
                data=kpi_frequency[0].daily_data,
                target_month=self.target_month,
                target_date=self.target_date,
                for_month=False,
            )
            return self.get_percentage(
                base_value=target_count, actual_value=actual_count
            )

        is_percentage = False if self.kpi_obj.unit_type == KPI.EURO_UNIT else True
        target_count, actual_count = self.count_target_actual_for_related_kpi(
            related_kpi_frequencies=related_kpi_frequencies,
            for_month=False,
            target_month=self.target_month,
            target_date=self.target_date,
            is_percentage=is_percentage,
        )
        return self.get_percentage(base_value=target_count, actual_value=actual_count)

    def count_target_actual_until_date_data(self, data):
        """This function will calcualte the data of the todays date"""
        target_count = 0
        actual_count = 0
        for entry in data:
            entry_date = datetime.datetime.strptime(entry["name"], "%d/%m/%Y").date()

            target_count += entry["target"]
            actual_count += entry["actual"]
            if entry_date == datetime.datetime.today().date():
                break
        return target_count, actual_count

    def calculate_total_ytd_data(self, obj, year) -> int:
        """This will calculate the YTD data"""
        kpi_frequency = (
            self.list_all_kpi_frequency(user=self.user)
            .filter(kpi_id=self.kpi_obj.id)
            .annotate(
                year=Subquery(
                    CalenderManager.objects.filter(
                        id=OuterRef("calender_manager_id")
                    ).values("year")
                )
            )
            .filter(year=year)
        )
        if kpi_frequency:
            target_count, actual_count = self.count_target_actual_until_date_data(
                kpi_frequency[0].daily_data
            )
            percentage = self.get_percentage(
                base_value=target_count, actual_value=actual_count
            )

            return target_count, actual_count, percentage
        return 0, 0, 0

    def calculate_quartely_data(self, obj, year) -> int:
        """This will calculate the Quarterly data"""
        kpi_data = {"target": {}, "actual": {}, "percentage": {}}
        kpi_frequency = (
            self.list_all_kpi_frequency(user=self.user)
            .filter(kpi_id=self.kpi_obj.id)
            .annotate(
                year=Subquery(
                    CalenderManager.objects.filter(
                        id=OuterRef("calender_manager_id")
                    ).values("year")
                )
            )
            .filter(year=year)
        )
        if kpi_frequency:
            for data in kpi_frequency[0].quarterly_data:
                data["percentage"] = self.get_percentage(
                    base_value=data["target"], actual_value=data["actual"]
                )
                kpi_data["target"].update(
                    {f'quarter_{data["quarter"]}_{year}': data["target"]}
                )
                kpi_data["actual"].update(
                    {f'quarter_{data["quarter"]}_{year}': data["actual"]}
                )
                kpi_data["percentage"].update(
                    {f'quarter_{data["quarter"]}_{year}': data["percentage"]}
                )

            return kpi_data
        else:
            for index in range(1, 5):
                kpi_data["target"].update({f"quarter_{index}_{year}": 0})
                kpi_data["actual"].update({f"quarter_{index}_{year}": 0})
                kpi_data["percentage"].update({f"quarter_{index}_{year}": 0})
            return kpi_data

    def calculate_monthly_data(self, obj, year) -> int:
        """This will calculate the Monthly data"""
        kpi_data = {"target": {}, "actual": {}, "percentage": {}}
        kpi_frequency = (
            self.list_all_kpi_frequency(user=self.user)
            .filter(kpi_id=self.kpi_obj.id)
            .annotate(
                year=Subquery(
                    CalenderManager.objects.filter(
                        id=OuterRef("calender_manager_id")
                    ).values("year")
                )
            )
            .filter(year=year)
        )
        if kpi_frequency:
            for data in kpi_frequency[0].monthly_data:
                data["percentage"] = self.get_percentage(
                    base_value=data["target"], actual_value=data["actual"]
                )
                kpi_data["target"].update(
                    {f'month_{data["month"]}_{year}': data["target"]}
                )
                kpi_data["actual"].update(
                    {f'month_{data["month"]}_{year}': data["actual"]}
                )
                kpi_data["percentage"].update(
                    {f'month_{data["month"]}_{year}': data["percentage"]}
                )
            return kpi_data
        else:
            for index in range(1, 13):
                kpi_data["target"].update({f"month_{index}_{year}": 0})
                kpi_data["actual"].update({f"month_{index}_{year}": 0})
                kpi_data["percentage"].update({f"month_{index}_{year}": 0})
            return kpi_data

    def calculate_yearly_data(self, obj, year) -> int:
        """This will calculate the Yearly data"""
        kpi_frequency = (
            self.list_all_kpi_frequency(user=self.user)
            .filter(kpi_id=self.kpi_obj.id)
            .annotate(
                year=Subquery(
                    CalenderManager.objects.filter(
                        id=OuterRef("calender_manager_id")
                    ).values("year")
                )
            )
            .filter(year=year)
        )
        if kpi_frequency:
            target_count, actual_count = (
                kpi_frequency[0].yearly_data[0]["target"],
                kpi_frequency[0].yearly_data[0]["actual"],
            )
            percentage = self.get_percentage(
                base_value=target_count, actual_value=actual_count
            )
            return target_count, actual_count, percentage
        return 0, 0, 0

    def list_kpi_frequency_by_year(self, year) -> QuerySet[KPIFrequency]:
        """This method will return list of KPI-Frequency."""
        return (
            self.kpi_frequency_services.get_kpi_frequency_repo()
            .filter(is_active=True, is_archived=False)
            .annotate(
                year=Subquery(
                    CalenderManager.objects.filter(year__in=year).values("year")
                )
            )
            .values_list("kpi_id", flat=True)
            .order_by("year")
        )


class RelativeKPIAppServices(BaseAppServiceWithAttributeLogger):
    def __init__(self) -> None:
        self.kpi_services = KPIServices()
        self.relative_kpi_services = RelativeKPIServices()
        self.user_app_service = UserAppServices()

    def list_relative_kpis(self, kpi_id, user: User) -> QuerySet[RelativeKPI]:
        """This method will return list of KPI-Frequency."""
        return (
            self.relative_kpi_services.get_relative_kpi_repo()
            .filter(is_active=True, relative_kpi_id=kpi_id)
            .order_by(
                models.Case(
                    models.When(level=RelativeKPI.NOMINATOR, then=models.Value(1)),
                    models.When(level=RelativeKPI.DENOMINATOR, then=models.Value(2)),
                    default=models.Value(3),
                )
            )
        )

    def list_relative_absolute_kpis(self, kpi_id, user: User) -> QuerySet[KPI]:
        related_kpis_ids = self.list_relative_kpis(
            kpi_id=kpi_id, user=user
        ).values_list("absolute_kpi_id")
        related_kpis_ids = [
            str(related_kpi_id[0]) for related_kpi_id in related_kpis_ids
        ]
        return (
            self.kpi_services.get_kpi_repo()
            .filter(id__in=related_kpis_ids, is_active=True, is_archived=False)
            .order_by(
                models.Case(
                    *[
                        models.When(pk=pk, then=pos)
                        for pos, pk in enumerate(related_kpis_ids)
                    ]
                )
            )
            .annotate(parent_id=Value(kpi_id, output_field=CharField()))
            .annotate(level=Value("child", output_field=CharField()))
        )

    def update_relative_kpi(
        self, kpi: KPI, user: User, numerator_obj: KPI, denominator_obj: KPI
    ) -> bool:
        relative_kpis = self.list_relative_kpis(kpi_id=kpi.id, user=user)
        if relative_kpis.count() != 2:
            raise RelativeKPINotFoundException(
                "relative-kpi-exception", "Relative KPI not found", self.log
            )
        numerator_level_kpi = relative_kpis[0]
        numerator_level_kpi.absolute_kpi_id = numerator_obj.id
        numerator_level_kpi.save()
        denominator_level_kpi = relative_kpis[1]
        denominator_level_kpi.absolute_kpi_id = denominator_obj.id
        denominator_level_kpi.save()
        return True


def check_all_data_same_on_not(data):
    target_values = set()
    actual_values = set()

    for item in data:
        target_values.add(item["target"])
        actual_values.add(item["actual"])

    return len(target_values) == 1, len(actual_values) == 1
