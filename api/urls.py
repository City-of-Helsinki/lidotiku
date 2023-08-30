from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(
    r"counters/data",
    views.CountersWithLatestObservationsView,
    basename="counters-data",
)
router.register(r"counters", views.CounterViewSet, basename="counter")
router.register(r"observations", views.ObservationViewSet, basename="observation")
router.register(
    r"observations/aggregate",
    views.ObservationAggregateViewSet,
    basename="observation-aggregate",
)


urlpatterns = [
    path("", include(router.urls)),
]
