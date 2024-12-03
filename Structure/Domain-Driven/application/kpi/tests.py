import logging

from django.db.models.query import QuerySet

# django imports
from django.test import TestCase
from focus_power.application.kpi.services import KPIAppServices, RelativeKPIAppServices
from focus_power.application.roles.services import RolesAppServices
from focus_power.application.user.services import UserAppServices
from focus_power.domain.calender_manager.models import CalenderManager
from focus_power.domain.company.company_division.models import (
    CompanyDivisionFactory,
    CompanyID,
)
from focus_power.domain.company.models import CompanyFactory
from focus_power.domain.division.models import DivisionFactory, DivisionID
from focus_power.domain.division.user_division.models import (
    CompanyDivisionID,
    UserDivisionFactory,
    UserID,
)
from focus_power.domain.kpi.kpi_frequency.services import (
    KPIFrequencyFactory,
    KPIFrequencyServices,
)
from focus_power.domain.kpi.models import KPI, KPIFactory
from focus_power.domain.kpi.services import KPIServices
from focus_power.domain.role.user_role.models import RoleID, UserRoleFactory
from focus_power.domain.user.models import UserBasePermissions, UserPersonalData
from focus_power.domain.user.services import UserServices
from focus_power.infrastructure.logger.models import AttributeLogger
from scripts.calender_generator import generate_ten_years_calendar_data

from .test_helper import TestHelper, monthly_frequency

log = AttributeLogger(logging.getLogger(__name__))


class KPIAppServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate_ten_years_calendar_data()

        cls.calendar_manager_obj = CalenderManager.objects.get(year=2023)

        cls.u_data_01 = UserPersonalData(
            username="testuser@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testuser@example.com",
        )
        cls.user_password = "Test@1234"

        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        cls.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=cls.user_password,
                personal_data=cls.u_data_01,
                base_permissions=cls.u_permissions_01,
            )
        )
        cls.user_obj.save()

        cls.user_app_services = UserAppServices()
        cls.roles_app_service = RolesAppServices()
        cls.role = (
            cls.roles_app_service.role_services.get_role_factory().build_entity_with_id(
                name="CEO"
            )
        )
        cls.role.save()
        cls.company = CompanyFactory().build_entity_with_id(name="Test-Company")
        cls.company.save()
        cls.user_role = UserRoleFactory().build_entity_with_id(
            role_id=RoleID(value=cls.role.id),
            company_id=CompanyID(value=cls.company.id),
            user_id=UserID(value=cls.user_obj.id),
        )
        cls.user_role.save()
        cls.division = DivisionFactory().build_entity_with_id(name="Test-Division")
        cls.division.save()
        cls.company_division = CompanyDivisionFactory().build_entity_with_id(
            company_id=CompanyID(value=cls.company.id),
            division_id=DivisionID(value=cls.division.id),
        )
        cls.company_division.save()
        cls.user_division = UserDivisionFactory().build_entity_with_id(
            user_id=UserID(value=cls.user_obj.id),
            company_division_id=CompanyDivisionID(value=cls.company_division.id),
        )
        cls.user_division.save()

        cls.test_helper = TestHelper(log=log)
        cls.kpi_list = cls.test_helper.create_kpis(
            calendar_manager=cls.calendar_manager_obj, user=cls.user_obj, number=10
        )

        cls.kpi_id_list = [kpi.id for kpi in cls.kpi_list]
        cls.kpi_app_services = KPIAppServices()

        cls.kpi_frequency_factory = KPIFrequencyFactory()

    def test_list_kpi_for_users(self):
        list_kpis = self.kpi_app_services.list_kpi(user=self.user_obj)
        self.assertEqual(type(list_kpis), QuerySet)

    def test_list_absolute_kpis_for_users(self):
        list_absolute_kpi = self.kpi_app_services.list_absolute_kpis(user=self.user_obj)
        self.assertEqual(type(list_absolute_kpi), QuerySet)

    def test_create_kpi_with_frequency_from_dict(self):
        # create_kpi_with_frequency_from_dict
        (
            kpi_obj,
            is_absolute_kpi,
        ) = self.kpi_app_services.create_kpi_with_frequency_from_dict(
            data=dict(
                name="Test KPI",
                unit_type=KPI.ABSOLUTE,
                frequency=KPI.MONTHLY,
                logic_level=KPI.INCREASED,
                reporting_person_id=str(self.user_obj.id),
                absolute_kpis=[],
                unit="pi",
                kpi_frequencies=monthly_frequency,
                plan_frequency=KPI.MONTHLY,
                calender_manager_id=str(self.calendar_manager_obj.pk),
                year=2023,
            ),
            user=self.user_obj,
        )

        self.assertEqual(isinstance(kpi_obj, KPI), True)

        with self.assertRaises(Exception):
            # create with wrong unit type
            (
                kpi_obj,
                is_absolute_kpi,
            ) = self.kpi_app_services.create_kpi_with_frequency_from_dict(
                data=dict(
                    name="Test KPI",
                    unit_type=None,
                    frequency=KPI.MONTHLY,
                    logic_level=KPI.INCREASED,
                    reporting_person_id=str(self.user_obj.id),
                    absolute_kpis=[],
                    unit="pi",
                    kpi_frequencies=monthly_frequency,
                    plan_frequency=KPI.MONTHLY,
                    calender_manager_id=str(self.calendar_manager_obj.pk),
                    year=2023,
                ),
                user=self.user_obj,
            )

            # create with wrong reporting_person_id
            (
                kpi_obj,
                is_absolute_kpi,
            ) = self.kpi_app_services.create_kpi_with_frequency_from_dict(
                data=dict(
                    name="Test KPI",
                    unit_type=KPI.ABSOLUTE,
                    frequency=KPI.MONTHLY,
                    logic_level=KPI.INCREASED,
                    reporting_person_id="sdksjdkjsjkdjskdskdsjkdskdsdsd",
                    absolute_kpis=[],
                    unit="pi",
                    kpi_frequencies=monthly_frequency,
                    plan_frequency=KPI.MONTHLY,
                    calender_manager_id=str(self.calendar_manager_obj.pk),
                    year=2023,
                ),
                user=self.user_obj,
            )

    def test_update_kpi_frequency_values(self):
        existing_kpi = self.kpi_list[0]

        # update kpi from dict
        kpi = self.kpi_app_services.update_kpi_frequency_values(
            data=dict(kpi_frequencies=monthly_frequency, value_type="actual"),
            user=self.user_obj,
            kpi_id=str(existing_kpi.id),
            value_type="actual",
        )
        self.assertEqual(isinstance(kpi, bool), True)

    def test_update_reporting_person(self):
        existing_kpi = self.kpi_list[0]

        kpi = self.kpi_app_services.update_reporting_person(
            pk=existing_kpi.id,
            data=dict(reporting_person=str(self.user_obj.id)),
            user=self.user_obj,
        )

        self.assertIsInstance(kpi, KPI)

        with self.assertRaises(Exception):
            # update with wrong reporting_person_id
            kpi = self.kpi_app_services.update_reporting_person(
                pk=existing_kpi.id,
                data=dict(reporting_person="efe0ab98-d4c9-4b29-81de-f425d7056c57"),
                user=self.user_obj,
            )

            # update with wrong kpi id
            kpi = self.kpi_app_services.update_reporting_person(
                pk="9ad62b3e-c399-4474-8dbc-e5b89a98cb54",
                data=dict(reporting_person=str(self.user_obj.id)),
                user=self.user_obj,
            )

    def test_list_kpi_for_owners(self):
        list_owner_kpis = self.kpi_app_services.list_owner_kpi(user=self.user_obj)
        self.assertEqual(type(list_owner_kpis), QuerySet)

    def test_get_kpi_by_kpi_id(self):
        fetched_kpi = self.kpi_app_services.get_kpi_by_kpi_id(
            kpi_id=self.kpi_list[0].id
        )
        self.assertEqual(type(fetched_kpi), KPI)

    def test_list_kpi_by_user_id(self):
        list_user_kpis = self.kpi_app_services.list_kpi_by_user_id(
            user_id=self.user_obj.id, kpi_id_list=self.kpi_id_list
        )
        self.assertEqual(type(list_user_kpis), QuerySet)


class KPIFrequencyAppServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate_ten_years_calendar_data()

        cls.calendar_manager_obj = CalenderManager.objects.get(year=2023)

        cls.u_data_01 = UserPersonalData(
            username="testuser@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testuser@example.com",
        )
        cls.user_password = "Test@1234"

        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        cls.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=cls.user_password,
                personal_data=cls.u_data_01,
                base_permissions=cls.u_permissions_01,
            )
        )
        cls.user_obj.save()

        cls.user_app_services = UserAppServices()
        cls.roles_app_services = RolesAppServices()
        cls.role = cls.roles_app_services.role_services.get_role_factory().build_entity_with_id(
            name="CEO"
        )
        cls.role.save()

        cls.company = CompanyFactory().build_entity_with_id(name="Test-Company")
        cls.company.save()

        cls.user_role = UserRoleFactory().build_entity_with_id(
            role_id=RoleID(value=cls.role.id),
            company_id=CompanyID(value=cls.company.id),
            user_id=UserID(value=cls.user_obj.id),
        )
        cls.user_obj.save()

        cls.division = DivisionFactory().build_entity_with_id(name="Test-Division")
        cls.division.save()

        cls.company_division = CompanyDivisionFactory().build_entity_with_id(
            company_id=CompanyID(value=cls.company.id),
            division_id=DivisionID(value=cls.division.id),
        )
        cls.company_division.save()

        cls.user_division = UserDivisionFactory().build_entity_with_id(
            user_id=UserID(value=cls.user_obj.id),
            company_division_id=CompanyDivisionID(value=cls.company_division.id),
        )
        cls.user_division.save()

        cls.kpi = KPIFactory().build_entity_with_id(
            name="Test KPI",
            unit_type=KPI.ABSOLUTE,
            frequency=KPI.MONTHLY,
            logic_level=KPI.INCREASED,
            reporting_person_id=UserID(value=cls.user_obj.id),
            unit="PI",
            user_id=UserID(value=cls.user_obj.id),
        )
        cls.kpi.save()

        cls.test_helper = TestHelper(log=log)
        cls.kpi_frequency_list = cls.test_helper.create_kpi_frequencies(
            cls.kpi, cls.calendar_manager_obj, number=5
        )

        cls.kpi_app_services = KPIAppServices()

        cls.kpi_services = KPIServices()

        cls.kpi_frequency_factory = KPIFrequencyFactory()

        cls.kpi_frequency_services = KPIFrequencyServices()

    def test_list_kpi_frequency(self):
        list_all_kpi_frequency = (
            self.kpi_frequency_services.get_kpi_frequency_repo().filter(is_active=True)
        )
        self.assertEqual(type(list_all_kpi_frequency), QuerySet)

    def test_get_kpi_frequency_data_by_kpi_id(self):
        kpi_queryset = self.kpi_services.get_kpi_repo().filter(id=self.kpi.id)
        frequency = kpi_queryset[0].frequency
        kpi_frequency_queryset = self.kpi_frequency_list[0]
        frequency_data = getattr(kpi_frequency_queryset, f"{frequency}_data")

        self.assertEqual(frequency_data, monthly_frequency[0])

        with self.assertRaises(Exception):
            # get kpi frequency data with wrong kpi id
            kpi_queryset = self.kpi_services.get_kpi_repo().filter(
                id="9ad62b3e-c399-4474-8dbc-e5b89a98cb54"
            )
            frequency = kpi_queryset[0].frequency
            kpi_frequency_queryset = self.kpi_frequency_list[0]
            frequency_data = getattr(kpi_frequency_queryset, f"{frequency}_data")

            # get kpi frequency data with wrong kpi frequency
            kpi_queryset = self.kpi_services.get_kpi_repo().filter(id=self.kpi.id)
            frequency = kpi_queryset[0].frequency
            kpi_frequency_queryset = self.kpi_frequency_list[5]
            frequency_data = getattr(kpi_frequency_queryset, f"{frequency}_data")


class RelativeKPIAppServicesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate_ten_years_calendar_data()

        cls.calendar_manager_obj = CalenderManager.objects.get(year=2023)

        cls.u_data_01 = UserPersonalData(
            username="testuser@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testuser@example.com",
        )
        cls.user_password = "Test@1234"

        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        cls.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=cls.user_password,
                personal_data=cls.u_data_01,
                base_permissions=cls.u_permissions_01,
            )
        )
        cls.user_obj.save()

        cls.user_app_services = UserAppServices()
        cls.roles_app_service = RolesAppServices()
        cls.role = (
            cls.roles_app_service.role_services.get_role_factory().build_entity_with_id(
                name="CEO"
            )
        )
        cls.role.save()
        cls.company = CompanyFactory().build_entity_with_id(name="Test-Company")
        cls.company.save()
        cls.user_role = UserRoleFactory().build_entity_with_id(
            role_id=RoleID(value=cls.role.id),
            company_id=CompanyID(value=cls.company.id),
            user_id=UserID(value=cls.user_obj.id),
        )
        cls.user_role.save()
        cls.division = DivisionFactory().build_entity_with_id(name="Test-Division")
        cls.division.save()
        cls.company_division = CompanyDivisionFactory().build_entity_with_id(
            company_id=CompanyID(value=cls.company.id),
            division_id=DivisionID(value=cls.division.id),
        )
        cls.company_division.save()
        cls.user_division = UserDivisionFactory().build_entity_with_id(
            user_id=UserID(value=cls.user_obj.id),
            company_division_id=CompanyDivisionID(value=cls.company_division.id),
        )
        cls.user_division.save()

        cls.test_helper = TestHelper(log=log)
        cls.relative_kpi_list = cls.test_helper.create_relative_kpis(
            calendar_manager=cls.calendar_manager_obj, user=cls.user_obj, number=1
        )

        cls.relative_kpi_app_services = RelativeKPIAppServices()

    def test_list_relative_kpis(self):
        list_relative_kpi = self.relative_kpi_app_services.list_relative_kpis(
            kpi_id=self.relative_kpi_list[0].id, user=self.user_obj
        )
        self.assertEqual(type(list_relative_kpi), QuerySet)

    def test_list_relative_absolute_kpis(self):
        list_relative_absolute_kpi = (
            self.relative_kpi_app_services.list_relative_absolute_kpis(
                kpi_id=self.relative_kpi_list[0].id, user=self.user_obj
            )
        )
        self.assertEqual(type(list_relative_absolute_kpi), QuerySet)
