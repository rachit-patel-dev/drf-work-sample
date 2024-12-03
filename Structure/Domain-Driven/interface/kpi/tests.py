import logging

from faker import Faker
from focus_power.application.kpi.services import KPIAppServices
from focus_power.application.kpi.test_helper import (
    TestHelper,
    monthly_frequency,
    wrong_monthly_frequency,
)
from focus_power.application.objective.test_helper import (
    TestHelper as ObjectiveTestHelper,
)
from focus_power.application.roles.services import RolesAppServices
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
from focus_power.domain.kpi.models import KPI, RelativeKPI
from focus_power.domain.role.user_role.models import RoleID, UserRoleFactory
from focus_power.domain.user.models import UserBasePermissions, UserPersonalData
from focus_power.domain.user.services import UserServices
from focus_power.infrastructure.logger.models import AttributeLogger
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate
from scripts.calender_generator import generate_ten_years_calendar_data

from .views import KPIViewSet

fake = Faker()
log = AttributeLogger(logging.getLogger(__name__))


class KPIViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Setup method for UserViewSetTestCase.
        """
        generate_ten_years_calendar_data()
        cls.calendar_manager_obj = CalenderManager.objects.get(year=2023)

        cls.u_data_01 = UserPersonalData(
            username="testerman@example.com",
            first_name="Testerman",
            last_name="Testerson",
            email="testerman@example.com",
        )
        cls.user_password = "Test@1234"
        cls.u_permissions_01 = UserBasePermissions(is_staff=False, is_active=True)

        cls.factory = APIRequestFactory()
        cls.kpi_view_set = KPIViewSet

        cls.user_obj = (
            UserServices()
            .get_user_factory()
            .build_entity_with_id(
                password=cls.user_password,
                personal_data=cls.u_data_01,
                base_permissions=cls.u_permissions_01,
            )
        )

        cls.expected_response_fields = ["success", "message", "data"]
        cls.expected_response_fields_with_errors = cls.expected_response_fields + [
            "errors"
        ]
        cls.expected_response_fields_of_data = [
            "count",
            "next",
            "previous",
            "results",
            "current_week",
        ]

        cls.user_obj.save()

        # user role and company creation

        cls.role_app_services = RolesAppServices()
        cls.role = (
            cls.role_app_services.role_services.get_role_factory().build_entity_with_id(
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

        # create_reporting_persons
        cls.objective_test_helper = ObjectiveTestHelper(log=log)
        (
            cls.reporting_persons,
            cls.user_divisions,
            cls.user_roles,
        ) = cls.objective_test_helper.create_user_roles()

        # create kpi list
        cls.test_helper = TestHelper(log=log)

        cls.kpi_list = cls.test_helper.create_kpis(
            calendar_manager=cls.calendar_manager_obj,
            user=cls.reporting_persons[2],
            number=6,
        )

        # kpi services
        cls.kpi_app_services = KPIAppServices()

    def test_create_kpi(self):
        expected_response_keys = [
            "id",
            "is_active",
            "name",
            "unit_type",
            "frequency",
            "logic_level",
            "unit",
            "plan_frequency",
            "user_id",
        ]
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": "PI",
            "kpi_frequencies": monthly_frequency,
            "absolute_kpis": [],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)
        self.assertListEqual(
            list(response.data.get("data").keys()), expected_response_keys
        )
        self.assertListEqual(list(response.data.keys()), self.expected_response_fields)

        # create percentage KPI
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.PERCENTAGE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": None,
            "kpi_frequencies": [],
            "absolute_kpis": [
                {
                    "absolute_kpi_id": str(self.kpi_list[0].id),
                    "level": RelativeKPI.NOMINATOR,
                },
                {
                    "absolute_kpi_id": str(self.kpi_list[1].id),
                    "level": RelativeKPI.DENOMINATOR,
                },
            ],
            "calender_manager_id": None,
            "plan_frequency": None,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)

        # create euro/unit KPI
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.EURO_UNIT,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": None,
            "kpi_frequencies": [],
            "absolute_kpis": [
                {
                    "absolute_kpi_id": str(self.kpi_list[0].id),
                    "level": RelativeKPI.NOMINATOR,
                },
                {
                    "absolute_kpi_id": str(self.kpi_list[1].id),
                    "level": RelativeKPI.DENOMINATOR,
                },
            ],
            "calender_manager_id": None,
            "plan_frequency": None,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)

        # create kpi without authentication
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 401)

        # create kpi without unit
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "kpi_frequencies": monthly_frequency,
            "absolute_kpis": [],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 422)
        self.assertEquals(response.data.get("success"), False)

        # create kpi with wrong reporting person
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": "f2dca97f-2bbe-451d-948b-04fc2365db9a",
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": "PI",
            "kpi_frequencies": monthly_frequency,
            "absolute_kpis": [],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 404)
        self.assertEquals(response.data.get("success"), False)

        # create percentage KPI without absolute KPI
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.PERCENTAGE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": None,
            "kpi_frequencies": [],
            "absolute_kpis": [],
            "calender_manager_id": None,
            "plan_frequency": None,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data.get("success"), False)

        # create absolute KPI with absolute KPIs
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": "PI",
            "kpi_frequencies": monthly_frequency,
            "absolute_kpis": [
                {
                    "absolute_kpi_id": str(self.kpi_list[0].id),
                    "level": RelativeKPI.NOMINATOR,
                },
                {
                    "absolute_kpi_id": str(self.kpi_list[1].id),
                    "level": RelativeKPI.DENOMINATOR,
                },
            ],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data.get("success"), False)

        # create KPI with wrong kpi_frequencies
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": "PI",
            "kpi_frequencies": wrong_monthly_frequency,
            "absolute_kpis": [],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data.get("success"), False)

        # create KPI without kpi_frequencies
        kpi_creation_data = {
            "name": fake.name(),
            "reporting_person_id": self.reporting_persons[0].id,
            "unit_type": KPI.ABSOLUTE,
            "frequency": KPI.MONTHLY,
            "logic_level": KPI.INCREASED,
            "unit": "PI",
            "kpi_frequencies": None,
            "absolute_kpis": [],
            "calender_manager_id": self.calendar_manager_obj.id,
            "plan_frequency": KPI.MONTHLY,
            "year": 2023,
        }
        request = self.factory.post(
            "/api/v0/kpi/", data=kpi_creation_data, format="json"
        )
        force_authenticate(request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"post": "create"})(request)
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.data.get("success"), False)

    def test_absolute_kpi_list(self):
        request = self.factory.get("/api/v0/kpi/absolute_kpi_list/")
        force_authenticate(request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"get": "absolute_kpi_list"})(request)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)
        self.assertListEqual(list(response.data.keys()), self.expected_response_fields)

        # list without authentication
        request = self.factory.get("/api/v0/kpi/absolute_kpi_list/")
        response = self.kpi_view_set.as_view({"get": "absolute_kpi_list"})(request)

        self.assertEquals(response.status_code, 401)

    def test_list(self):
        request = self.factory.get("/api/v0/kpi/")
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"get": "list"})(request)

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)
        self.assertListEqual(list(response.data.keys()), self.expected_response_fields)
        self.assertListEqual(
            list(response.data.get("data").keys()),
            self.expected_response_fields_of_data,
        )

        # list without authentication
        request = self.factory.get("/api/v0/kpi/")
        response = self.kpi_view_set.as_view({"get": "list"})(request)

        self.assertEquals(response.status_code, 401)

    def test_related_absolute_kpi_list(self):
        request = self.factory.get(
            f"/api/v0/kpi/{self.kpi_list[0].id}/related_absolute_kpi_list/"
        )
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"get": "related_absolute_kpi_list"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)
        self.assertListEqual(list(response.data.keys()), self.expected_response_fields)

        # list without authentication
        request = self.factory.get("/api/v0/related_absolute_kpi_list/")
        response = self.kpi_view_set.as_view({"get": "related_absolute_kpi_list"})(
            request
        )

        self.assertEquals(response.status_code, 401)

    def test_get_frequency_for_absolute_kpi(self):
        request = self.factory.get(
            f"/api/v0/kpi/{self.kpi_list[0].id}/get_frequency_for_absolute_kpi/"
        )
        force_authenticate(request=request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"get": "get_frequency_for_absolute_kpi"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data.get("success"), True)
        self.assertListEqual(list(response.data.keys()), self.expected_response_fields)

        # list without authentication
        request = self.factory.get(
            f"/api/v0/kpi/{self.kpi_list[0].id}/get_frequency_for_absolute_kpi/"
        )
        response = self.kpi_view_set.as_view({"get": "get_frequency_for_absolute_kpi"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 401)

        # list with wrong absolute kpi
        request = self.factory.get(
            "/api/v0/kpi/f2dca97f-2bbe-451d-948b-04fc2365db9a/get_frequency_for_absolute_kpi/"
        )
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"get": "get_frequency_for_absolute_kpi"})(
            request, pk="f2dca97f-2bbe-451d-948b-04fc2365db9a"
        )

        self.assertEquals(response.status_code, 404)

    def test_update_values_of_frequency_data(self):
        update_data = {
            "kpi_frequencies": monthly_frequency,
            "value_type": "actual",
        }
        request = self.factory.put(
            f"/api/v0/kpi/{self.kpi_list[0].id}/update_values_of_frequency_data/",
            data=update_data,
            format="json",
        )
        force_authenticate(request=request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view(
            {"put": "update_values_of_frequency_data"}
        )(request, pk=self.kpi_list[0].id)

        self.assertEquals(response.status_code, 200)

        # update with wrong absolute kpi
        request = self.factory.put(
            "/api/v0/kpi/f2dca97f-2bbe-451d-948b-04fc2365db9a/update_values_of_frequency_data/",
            data=update_data,
            format="json",
        )
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view(
            {"put": "update_values_of_frequency_data"}
        )(request, pk="f2dca97f-2bbe-451d-948b-04fc2365db9a")

        self.assertEquals(response.status_code, 404)

        # update with wrong kpi frequencies
        update_incorrect_data = {
            "kpi_frequencies": wrong_monthly_frequency,
            "value_type": "actual",
        }
        request = self.factory.put(
            f"/api/v0/kpi/{self.kpi_list[0].id}/update_values_of_frequency_data/",
            data=update_incorrect_data,
            format="json",
        )
        force_authenticate(request=request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view(
            {"put": "update_values_of_frequency_data"}
        )(request, pk=self.kpi_list[0].id)

        self.assertEquals(response.status_code, 422)

    def test_update_reporting_person(self):
        update_data = {"reporting_person": self.reporting_persons[0].id}

        request = self.factory.put(
            f"/api/v0/kpi/{self.kpi_list[0].id}/update_reporting_person/",
            data=update_data,
            format="json",
        )
        force_authenticate(request=request, user=self.reporting_persons[0])
        response = self.kpi_view_set.as_view({"put": "update_reporting_person"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 200)

        # update without authentication
        request = self.factory.put(
            f"/api/v0/kpi/{self.kpi_list[0].id}/update_reporting_person/",
            data=update_data,
            format="json",
        )
        response = self.kpi_view_set.as_view({"put": "update_reporting_person"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 401)

        # update with wrong reporting_person_id
        wrong_reporting_person_data = {
            "reporting_person": "efe0ab98-d4c9-4b29-81de-f425d7056c57"
        }

        request = self.factory.put(
            f"/api/v0/kpi/{self.kpi_list[0].id}/update_reporting_person/",
            data=wrong_reporting_person_data,
            format="json",
        )
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"put": "update_reporting_person"})(
            request, pk=self.kpi_list[0].id
        )

        self.assertEquals(response.status_code, 404)

        # update with wrong kpi id
        request = self.factory.put(
            f"/api/v0/kpi/9ad62b3e-c399-4474-8dbc-e5b89a98cb54/update_reporting_person/",
            data=update_data,
            format="json",
        )
        force_authenticate(request=request, user=self.user_obj)
        response = self.kpi_view_set.as_view({"put": "update_reporting_person"})(
            request, pk="9ad62b3e-c399-4474-8dbc-e5b89a98cb54"
        )

        self.assertEquals(response.status_code, 404)
