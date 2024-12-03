import os
import sys

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "focus_power.settings")
BROKER_BACKEND = settings.CELERY_BROKER_URL

if "test" in sys.argv[1:]:
    BROKER_BACKEND = "memory://localhost"

app = Celery(
    "focus_power",
    broker=BROKER_BACKEND,
    backend="redis://",
    include=[
        "focus_power.application.recurring_activities.tasks",
        "focus_power.application.forecast.tasks",
        "focus_power.application.kpi.tasks",
        "focus_power.application.review.tasks",
    ],
    task_acks_late=True,
    task_acks_on_failure_or_timeout=False,
    task_reject_on_worker_lost=True,
)

app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    "run-at-every-day": {
        "task": "focus_power.application.recurring_activities.tasks.create_activity_records_for_never_ending_activity",
        "schedule": crontab(
            minute="*",
            hour="*",
            day_of_week="*",
        ),
    },
    "run-at-every-month-first-day": {
        "task": "focus_power.application.forecast.tasks.create_empty_forecast_entry_into_db",
        "schedule": crontab(
            minute="0",
            hour="0",
            day_of_month="28",
            day_of_week="*",
            month_of_year="*",
        ),
    },
    "run-at-every-day-to-create-activity-in-batch-of-five": {
        "task": "focus_power.application.recurring_activities.tasks.create_activity_records_in_batch_of_five",
        "schedule": crontab(
            minute="*",
            hour="*",
            day_of_week="*",
        ),
    },
    "run-at-first-of-december-to-create-kpis": {
        "task": "focus_power.application.kpi.tasks.create_kpi_for_next_year",
        "schedule": crontab(
            minute="0",
            hour="0",
            day_of_month="1",
            month_of_year="12",
        ),
    },
    "run-at-first-of-december-to-create-reviews": {
        "task": "focus_power.application.review.tasks.create_review_for_next_year",
        "schedule": crontab(
            minute="0",
            hour="0",
            day_of_month="1",
            month_of_year="12",
        ),
    },
    "run-one-day-ago-from-last-day-of-year-generate-planning-overviews": {
        "task": "focus_power.application.planning.tasks.create_planning_and_overview_for_each_organization",
        "schedule": crontab(minute=0, hour=0, day_of_month=1, month_of_year=1),
    },
}

if __name__ == "__main__":
    app.start()
