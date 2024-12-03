import logging
import uuid

from django.db.models.manager import Manager
from django.test import TestCase
from focus_power.domain.division.user_division.models import UserID
from focus_power.domain.user.models import UserBasePermissions, UserPersonalData
from focus_power.domain.user.services import UserServices
from focus_power.infrastructure.logger.models import AttributeLogger

from .models import (
    KPI,
    KPIID,
    KPIFactory,
    RelativeKPI,
    RelativeKPIFactory,
    RelativeKPIID,
)
from .services import KPIServices, RelativeKPIServices

log = AttributeLogger(logging.getLogger(__name__))


class KPITests(TestCase):
    def setUp(self):
        self.u_data_01 = UserPersonalData(
            username="testuser@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testuser@example.com",
        )
        self.user_password = "Test@1234"
        self.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        self.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=self.user_password,
                personal_data=self.u_data_01,
                base_permissions=self.u_permissions_01,
            )
        )
        self.user_obj.save()

        self.kpi = KPIFactory().build_entity_with_id(
            name="Test KPI",
            unit_type=KPI.ABSOLUTE,
            frequency=KPI.MONTHLY,
            logic_level=KPI.INCREASED,
            reporting_person_id=UserID(value=self.user_obj.id),
            unit="pi",
            user_id=UserID(value=self.user_obj.id),
        )
        self.kpi.save()

    def test_build_kpi_id(self):
        kpi_id = KPIID(value=uuid.uuid4())
        self.assertEqual(type(kpi_id), KPIID)

    def test_kpi_instance(self):
        self.assertIsInstance(self.kpi, KPI)


class KPIServicesTests(TestCase):
    def test_get_kpi_repo(self):
        repo = KPIServices().get_kpi_repo()
        self.assertEqual(Manager, type(repo))

    def test_get_kpi_factory(self):
        factory = KPIServices().get_kpi_factory()
        self.assertEqual(KPIFactory, factory)


class RelativeKPITests(TestCase):
    def setUp(self):
        self.u_data_01 = UserPersonalData(
            username="testuser@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testuser@example.com",
        )
        self.user_password = "Test@1234"
        self.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        self.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=self.user_password,
                personal_data=self.u_data_01,
                base_permissions=self.u_permissions_01,
            )
        )
        self.user_obj.save()

        self.kpi_01 = KPIFactory().build_entity_with_id(
            name="Test KPI 01",
            unit_type=KPI.ABSOLUTE,
            frequency=KPI.MONTHLY,
            logic_level=KPI.INCREASED,
            reporting_person_id=UserID(value=self.user_obj.id),
            unit="XY",
            user_id=UserID(value=self.user_obj.id),
        )
        self.kpi_01.save()

        self.kpi_02 = KPIFactory().build_entity_with_id(
            name="Test KPI 02",
            unit_type=KPI.ABSOLUTE,
            frequency=KPI.MONTHLY,
            logic_level=KPI.INCREASED,
            reporting_person_id=UserID(value=self.user_obj.id),
            unit="PI",
            user_id=UserID(value=self.user_obj.id),
        )
        self.kpi_02.save()

        self.kpi_03 = KPIFactory().build_entity_with_id(
            name="Test KPi 03",
            unit_type=KPI.PERCENTAGE,
            frequency=KPI.MONTHLY,
            logic_level=KPI.INCREASED,
            reporting_person_id=UserID(value=self.user_obj.id),
            user_id=UserID(value=self.user_obj.id),
        )
        self.kpi_03.save()

        self.relative_kpi_01 = RelativeKPIFactory().build_entity_with_id(
            relative_kpi_id=KPIID(value=self.kpi_03.id),
            absolute_kpi_id=KPIID(value=self.kpi_01.id),
            level=RelativeKPI.NOMINATOR,
        )
        self.relative_kpi_01.save()

        self.relative_kpi_02 = RelativeKPIFactory().build_entity_with_id(
            relative_kpi_id=KPIID(value=self.kpi_03.id),
            absolute_kpi_id=KPIID(value=self.kpi_02.id),
            level=RelativeKPI.NOMINATOR,
        )
        self.relative_kpi_02.save()

    def test_build_relative_kpi_id(self):
        relative_kpi_id = RelativeKPIID(value=uuid.uuid4())
        self.assertEqual(type(relative_kpi_id), RelativeKPIID)

    def test_relative_kpi_instance(self):
        self.assertIsInstance(self.relative_kpi_01, RelativeKPI)
        self.assertIsInstance(self.relative_kpi_02, RelativeKPI)


class RelativeKPIServicesTest(TestCase):
    def test_get_relative_kpi_repo(self):
        repo = RelativeKPIServices().get_relative_kpi_repo()
        self.assertEqual(Manager, type(repo))

    def test_get_relative_kpi_factory(self):
        factory = RelativeKPIServices().get_relative_kpi_factory()
        self.assertEqual(RelativeKPIFactory, factory)
