### `Custom scripts will be used to do operations with some data or some data loaders`

# Populate Organization Data Script

## Description

The 'Code-Under-Test' is a script designed to populate a database with organization data. It performs various tasks such as creating companies, divisions, roles, users, and assigning roles and divisions to users.

## Inputs

- **organizations**: a list of organization names
- **DIVISION**: a string representing the name of the division
- **OWNER_EMAIL**: a string representing the email format for company owners
- **OWNER_PASSWORD**: a string representing the password for company owners
- **ROLE**: a string representing the name of the role

## Flow

1. The script begins by importing necessary modules and defining constants.
2. The `populate_companies` function creates company objects and their corresponding divisions.
3. The `populate_company_owners` function creates user objects for company owners and assigns them roles and forecast data.
4. The `populate_divisions` function creates division objects.
5. The `populate_company_division` function assigns divisions to companies.
6. The `populate_roles` function creates role objects.
7. The `populate_user_roles` function creates user objects and assigns them roles and divisions.
8. The `remove_all_data` function deletes all existing data from the database.
9. The `populate_all_organization_data` function reads organization data from a JSON file and populates the database using the previously defined functions.
10. The `run` function executes the `populate_all_organization_data` function and prints a success message.

## Outputs

None

## Usage Example

```bash
python manage.py runscript populate_organization_data
```

This command will execute the `run` function in the script, which will populate the database with organization data.
```