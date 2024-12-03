import json
import os
from datetime import datetime
from typing import List, Tuple

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from faker import Faker
from focus_power.application.forecast.services import generate_initial_forecast_data
from focus_power.domain.company.company_division.models import CompanyDivision
from focus_power.domain.company.models import Company
from focus_power.domain.direct_report.services import DirectReportServices
from focus_power.domain.division.models import Division
from focus_power.domain.division.user_division.models import UserDivision
from focus_power.domain.forecast.models import Forecast
from focus_power.domain.objective.models import Objective
from focus_power.domain.objective.objectivecondition.models import ObjectiveCondition
from focus_power.domain.role.models import Role
from focus_power.domain.role.user_role.models import UserRole
from focus_power.domain.user.models import User
from utils.global_methods.global_value_objects import UserID

fake = Faker()
OWNER_EMAIL = os.environ.get("OWNER_EMAIL")
OWNER_PASSWORD = os.environ.get("OWNER_PASSWORD")
ROLE = os.environ.get("ROLE")
DIVISION = os.environ.get("DIVISION")


def populate_companies(
    organizations: list,
) -> Tuple[List[Company], List[CompanyDivision]]:
    companies = []
    company_divisions = []
    division = Division.objects.create(name=DIVISION)
    for organization_count in range(len(organizations)):
        obj = Company.objects.create(name=organizations[organization_count])
        company_divisions.append(
            CompanyDivision.objects.create(division_id=division.id, company_id=obj.id)
        )
        print(f"{organizations[organization_count]} is created")
        companies.append(obj)
    print("populated-companies successfully")
    return companies, company_divisions


def populate_company_owners(
    companies: List[Company], company_divisions: List[CompanyDivision]
) -> Tuple[List[User], List[UserRole]]:
    """
Populate company owners.

This function populates the owners of the companies with the provided information.

Parameters:
- companies (List[Company]): A list of Company objects representing the companies.
- company_divisions (List[CompanyDivision]): A list of CompanyDivision objects representing the divisions of the companies.

Returns:
- Tuple[List[User], List[UserRole]]: A tuple containing two lists. The first list contains the created User objects representing the owners, and the second list contains the created UserRole objects.

"""
    owners = []
    user_roles = []
    role = Role.objects.create(name=ROLE)
    current_year = datetime.now().year
    current_month = datetime.now().month
    forecast_data = generate_initial_forecast_data(current_year, current_month)
    direct_report_factory_method = DirectReportServices().get_direct_report_factory()
    for company_count in range(len(companies)):
        obj = User.objects.create(
            email=OWNER_EMAIL.format(company_count + 1),
            username=OWNER_EMAIL.format(company_count + 1),
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            password=make_password(OWNER_PASSWORD),
            is_verified=True,
        )
        forecast_obj = Forecast.objects.create(
            name="Revenue",
            company_id=companies[company_count].id,
            forecast_data=forecast_data,
            owner_id=obj.id,
        )
        print(
            f"{forecast_obj.name} is created for company {companies[company_count].id}"
        )
        direct_report_obj = direct_report_factory_method.build_entity_with_id(
            user_id=UserID(value=obj.id)
        )
        direct_report_obj.save()
        print(f"{obj.email} is created")
        print(f"{obj.email}'s direct report is created")
        owners.append(obj)
        user_role = UserRole.objects.create(
            role_id=role.id, user_id=obj.id, company_id=companies[company_count].id
        )
        for company_division in company_divisions:
            if companies[company_count].id == company_division.company_id:
                UserDivision.objects.create(
                    company_division_id=company_division.id, user_id=obj.id
                )
        print(f"{obj.email}'s {role.name} is created")
        user_roles.append(user_role)
    print("populate_company_owners successfully")
    return owners, user_roles


def populate_divisions(divisions: list) -> List[Division]:
    division_list = []
    for division in divisions:
        division_list.append(Division.objects.create(name=division))
        print(f"{division} is created")
    print("populate_divisions successfully")
    return division_list


def populate_company_division(
    companies: List[Company], divisions: List[Division]
) -> List[CompanyDivision]:
    company_divisions = []
    for company in companies:
        for division in divisions:
            company_divisions.append(
                CompanyDivision.objects.create(
                    division_id=division.id, company_id=company.id
                )
            )
            print(f"{company.name}'s {division.name} is created")
    print("populate_company_division successfully")
    return company_divisions


def populate_roles(roles: list) -> List[Role]:
    role_list = []
    for role in roles:
        role_list.append(Role.objects.create(name=role))
        print(f"{role} is created")

    print("populate_roles successfully")
    return role_list


def populate_user_roles(
    company_divisions: List[CompanyDivision], roles: List[Role]
) -> Tuple[List[User], List[UserDivision], List[UserRole]]:
    user_roles = []
    users = []
    division_users = []
    direct_report_factory_method = DirectReportServices().get_direct_report_factory()
    for division in company_divisions:
        for role in roles:
            email = fake.email().split("@")[0] + "@yopmail.com"
            user_obj = User.objects.create(
                email=email,
                username=email,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password=make_password(OWNER_PASSWORD),
                is_verified=True,
            )
            direct_report_obj = direct_report_factory_method.build_entity_with_id(
                user_id=UserID(value=user_obj.id)
            )
            direct_report_obj.save()
            print(f"{user_obj.email} is created")
            print(f"{user_obj.email}'s direct report is created")

            users.append(user_obj)
            division_users.append(
                UserDivision.objects.create(
                    company_division_id=division.id, user_id=user_obj.id
                )
            )
            print(f"{division.division_id} is created")

            user_roles.append(
                UserRole.objects.create(
                    role_id=role.id, user_id=user_obj.id, company_id=division.company_id
                )
            )
            print(f"{user_obj.email}'s role {role.name} is created")
    print("populate_user_roles successfully")
    return users, division_users, user_roles


def remove_all_data():
    print("started--------")
    User.objects.all().exclude(is_staff=True, is_superuser=True).delete()
    Division.objects.all().delete()
    UserDivision.objects.all().delete()
    Role.objects.all().delete()
    UserRole.objects.all().delete()
    Company.objects.all().delete()
    CompanyDivision.objects.all().delete()
    Objective.objects.all().delete()
    ObjectiveCondition.objects.all().delete()
    print("removed---all----data")


def populate_all_organization_data():
    with open(f"{settings.BASE_DIR}/scripts/organization_data.json", "r") as f:
        organization_data = json.load(f)
        organizations = organization_data.get("organization")
        divisions = organization_data.get("divisions")
        roles = organization_data.get("roles")

        with transaction.atomic():
            remove_all_data()
            companies, company_divisions = populate_companies(
                organizations=organizations
            )
            company_users, company_user_roles = populate_company_owners(
                companies=companies, company_divisions=company_divisions
            )
            division_list = populate_divisions(divisions=divisions)
            company_divisions = populate_company_division(
                companies=companies, divisions=division_list
            )
            roles_list = populate_roles(roles=roles)
            populate_user_roles(company_divisions=company_divisions, roles=roles_list)


def run():
    populate_all_organization_data()
    print("Successfully populated organization data")


# use of this script

# python manage.py runscript <script-name>
