from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"counters", views.CounterViewSet, basename="counter")
router.register(r"observations", views.ObservationViewSet, basename="observation")
router.register(
    r"observations/aggregate",
    views.ObservationAggregateViewSet,
    basename="observation-aggregate",
)
router.register(r"metadata/sources", views.DatasourcesViewSet, basename="sources")


urlpatterns = [
    path("", include(router.urls)),
]
