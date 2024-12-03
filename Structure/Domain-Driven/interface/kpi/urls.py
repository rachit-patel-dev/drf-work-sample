from focus_power.interface.kpi.views import KPIViewSet
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r"kpi", KPIViewSet, basename="kpi")
