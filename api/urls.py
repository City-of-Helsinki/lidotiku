from django.urls import include, path
from rest_framework_nested import routers
from . import views

router = routers.SimpleRouter()
router.register(
    r"counters/data",
    views.CountersWithLatestObservationsView,
    basename="counters-data",
)

router.register(r"counters", views.CounterViewSet)
data_router = routers.NestedSimpleRouter(router, r"counters", lookup="counter")
data_router.register(
    r"data", views.CounterWithLatestObservationsView, basename="counter-data"
)
router.register(r"observations", views.ObservationViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("", include(data_router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
