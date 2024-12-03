import logging

from focus_power.celery import app
from focus_power.domain.forecast.services import ForecastServices
from focus_power.infrastructure.logger.models import AttributeLogger

from .services import MONTH_LIST


def generate_next_month_forecast_response(current_year, current_month):
    """
    Generate the forecast data for the next 6 months based on the current year and month.

    Parameters:
    - current_year (int): The current year.
    - current_month (int): The current month.

    Returns:
    - forecast_data_list (list): A list of dictionaries containing the forecast data for each month. Each dictionary has the following keys:
        - "year" (str): The year of the forecast.
        - "month_name" (str): The name of the month for which the forecast is generated.
        - "for_month" (str): The name of the month for which the forecast is being made.
        - "for_year" (str): The year for which the forecast is being made.
        - "values" (dict): A dictionary containing the actual and forecast values for the month. The keys are "actual" and "forecast", and the values are empty strings.

    Example:
    >>> generate_next_month_forecast_response(2022, 9)
    [
        {
            "year": "2022",
            "month_name": "September",
            "for_month": "August",
            "for_year": "2022",
            "values": {"actual": "", "forecast": ""}
        },
        {
            "year": "2022",
            "month_name": "October",
            "for_month": "September",
            "for_year": "2022",
            "values": {"actual": "", "forecast": ""}
        },
        ...
    ]
    """
    # Create an empty forecast list
    forecast_data_list = []

    # Initialize the year and month
    year = current_year
    month = current_month

    for_month, for_year = month - 1, year
    for _ in range(6):
        if month > 11:
            month = 0
            year += 1
        if for_month > 11:
            for_month = 0
            for_year += 1
        # Create a dictionary for the current month's forecast data
        forecast_data = {
            "year": str(year),
            "month_name": MONTH_LIST[month],
            "for_month": MONTH_LIST[for_month],
            "for_year": str(for_year),
            "values": {"actual": "", "forecast": ""},
        }

        for_month += 1

        # Append the forecast data to the forecast_data_list
        forecast_data_list.append(forecast_data)

    return forecast_data_list


def generate_grouped_data_from_response(response_data):
    """
    Generate grouped data from the response data.

    Parameters:
    - response_data (list): A list of dictionaries containing the response data. Each dictionary represents a forecast data with the following keys:
        - "year" (str): The year of the forecast.
        - "month_name" (str): The name of the month for which the forecast is generated.
        - "for_month" (str): The name of the month for which the forecast is being made.
        - "for_year" (str): The year for which the forecast is being made.
        - "values" (dict): A dictionary containing the actual and forecast values for the month. The keys are "actual" and "forecast", and the values are empty strings.

    Returns:
    - final_forecast_response (dict): A dictionary containing the grouped and restructured forecast data. It has the following key:
        - "data" (list): A list of dictionaries representing the grouped forecast data. Each dictionary has the following keys:
            - "year" (str): The year of the forecast.
            - "month" (str): The name of the month for which the forecast is generated.
            - "month_index" (int): The index of the month in the MONTH_LIST.
            - "month_data" (list): A list of dictionaries representing the forecast data for the month.

    Example:
    >>> response_data = [
        {
            "year": "2022",
            "month_name": "September",
            "for_month": "August",
            "for_year": "2022",
            "values": {"actual": "", "forecast": ""}
        },
        {
            "year": "2022",
            "month_name": "October",
            "for_month": "September",
            "for_year": "2022",
            "values": {"actual": "", "forecast": ""}
        },
        ...
    ]
    >>> generate_grouped_data_from_response(response_data)
    {
        "data": [
            {
                "year": "2022",
                "month": "September",
                "month_index": 9,
                "month_data": [
                    {
                        "year": "2022",
                        "month_name": "September",
                        "for_month": "August",
                        "for_year": "2022",
                        "values": {"actual": "", "forecast": ""}
                    }
                ]
            },
            {
                "year": "2022",
                "month": "October",
                "month_index": 10,
                "month_data": [
                    {
                        "year": "2022",
                        "month_name": "October",
                        "for_month": "September",
                        "for_year": "2022",
                        "values": {"actual": "", "forecast": ""}
                    }
                ]
            },
            ...
        ]
    }
    """
    # Initialized empty array and list
    grouped_item_data = {}
    restructured_grouped_data = []

    # Group By data based on the year and month key combined
    for item in response_data:
        item_year = item.get("year")
        item_month_name = item.get("month_name")
        combined_month_year_key = f"{item_year}_{item_month_name}"
        if combined_month_year_key not in grouped_item_data:
            grouped_item_data[combined_month_year_key] = []
        grouped_item_data[combined_month_year_key].append(item)

    # Iterate through grouped_item_data and restructure the response
    for month, month_data in grouped_item_data.items():
        year, month = month.split("_")
        grouped_data = {}
        grouped_data["year"] = year
        grouped_data["month"] = month
        grouped_data["month_index"] = MONTH_LIST.index(month) + 1
        grouped_data["month_data"] = month_data
        restructured_grouped_data.append(grouped_data)

    # Finalize the response
    final_forecast_response = {
        "data": restructured_grouped_data,
    }

    # Return the response
    return final_forecast_response


@app.task
def create_empty_forecast_entry_into_db():
    """
    Create empty forecast entries in the database for the next year.

    This function fetches all forecasts from the database and generates empty forecast data for the next year. It iterates through each forecast, generates the forecast data using the 'generate_next_month_forecast_response' function, and saves the new month response in the database for the forecast.

    Returns:
        None

    Example:
        create_empty_forecast_entry_into_db()
    """
    log = AttributeLogger(logging.getLogger(__name__))
    try:
        log.info("STARTED_CREATING_EMPTY_FORECAST_DATA_FOR_NEXT_YEAR")

        # Initialize the forecast domain layer service
        forecast_services = ForecastServices()

        # Fetch all forecasts
        forecasts = forecast_services.get_forecast_repo()

        # Iterate through all forecast and save new month response in the database for the forecast
        for forecast in forecasts.all():
            grouped_data = generate_grouped_data_from_response(forecast.forecast_data)
            grouped_data_last_record = grouped_data["data"][-1]

            grouped_data_year = grouped_data_last_record["year"]
            grouped_data_month_index = MONTH_LIST.index(
                grouped_data_last_record["month"]
            )

            # generate_next_month_forecast_response
            response = generate_next_month_forecast_response(
                int(grouped_data_year), grouped_data_month_index + 1
            )
            forecast_data = getattr(forecast, "forecast_data")
            for data in response:
                forecast_data.append(data)
                setattr(forecast, "forecast_data", forecast_data)
                forecast.save()

        log.info("ENDED_CREATING_EMPTY_FORECAST_DATA_FOR_NEXT_YEAR")
    except Exception:
        pass
