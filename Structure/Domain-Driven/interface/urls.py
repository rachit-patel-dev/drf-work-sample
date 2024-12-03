"""focus_power URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from focus_power.interface.calender_manager.urls import router as calender_router
from focus_power.interface.direct_report.urls import router as direct_report_router
from focus_power.interface.division.urls import router as division_router
from focus_power.interface.document.urls import router as document_router
from focus_power.interface.forecast.urls import router as forecast_router
from focus_power.interface.general_settings.urls import (
    router as general_settings_router,
)
from focus_power.interface.initiative.urls import router as initiative_router
from focus_power.interface.kpi.urls import router as kpi_router
from focus_power.interface.kpi_reporting.urls import router as kpi_reporting_router
from focus_power.interface.objective.all_objective_listing.urls import (
    router as all_objective_router,
)
from focus_power.interface.objective.urls import router as objective_router
from focus_power.interface.page_level_permission.urls import (
    router as page_level_permission_router,
)
from focus_power.interface.planning.urls import router as planning_router
from focus_power.interface.prioritized_tasks.urls import (
    router as prioritized_tasks_router,
)
from focus_power.interface.process.urls import router as process_router
from focus_power.interface.recurring_activities.urls import (
    router as recurring_activity_router,
)
from focus_power.interface.reportee_tracker.urls import (
    router as reportee_tracker_router,
)
from focus_power.interface.review.urls import router as review_router
from focus_power.interface.role.urls import router as role_router
from focus_power.interface.user.urls import router as user_router

# from .user.views import GoogleAuthView


# import urls from interface layer modules

ENABLE_API = settings.ENABLE_API
PROJECT_URL = "/custom_admin"
API_SWAGGER_URL = settings.API_SWAGGER_URL
REDIRECTION_URL = API_SWAGGER_URL if settings.DEBUG else PROJECT_URL

# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("superadmin/", admin.site.urls),
    path("", RedirectView.as_view(url=REDIRECTION_URL, permanent=False)),
]

urlpatterns += [
    path(API_SWAGGER_URL, include(user_router.urls)),
    path(API_SWAGGER_URL, include(objective_router.urls)),
    path(API_SWAGGER_URL, include(all_objective_router.urls)),
    path(API_SWAGGER_URL, include(prioritized_tasks_router.urls)),
    path(API_SWAGGER_URL, include(reportee_tracker_router.urls)),
    path(API_SWAGGER_URL, include(kpi_router.urls)),
    path(API_SWAGGER_URL, include(calender_router.urls)),
    path(API_SWAGGER_URL, include(role_router.urls)),
    path(API_SWAGGER_URL, include(division_router.urls)),
    path(API_SWAGGER_URL, include(initiative_router.urls)),
    path(API_SWAGGER_URL, include(process_router.urls)),
    path(API_SWAGGER_URL, include(recurring_activity_router.urls)),
    path(API_SWAGGER_URL, include(kpi_reporting_router.urls)),
    path(API_SWAGGER_URL, include(forecast_router.urls)),
    path(API_SWAGGER_URL, include(document_router.urls)),
    path(API_SWAGGER_URL, include(review_router.urls)),
    path(API_SWAGGER_URL, include(general_settings_router.urls)),
    path(API_SWAGGER_URL, include(planning_router.urls)),
    path(API_SWAGGER_URL, include(direct_report_router.urls)),
    path(API_SWAGGER_URL, include(page_level_permission_router.urls)),
    # CUSTOM ADMIN URLS
    path("custom_admin/", include("custom_admin.urls")),
]
# media url

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += [
        path(
            API_SWAGGER_URL,
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path("api/v0/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("__debug__/", include(debug_toolbar.urls)),
    ]
