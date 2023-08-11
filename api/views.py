from itertools import groupby
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.db.models.query import QuerySet
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.measure import Distance as DistanceObject
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Counter, Observation, CounterWithLatestObservations
from .serializers import (
    CounterSerializer,
    ObservationSerializer,
    CounterDataSerializer,
)


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000


class CounterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for counters/sensors.
    """

    pagination_class = None

    serializer_class = CounterSerializer

    def get_queryset(self):
        queryset = Counter.objects.all()
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        distance = self.request.query_params.get("distance")
        if lat is not None and lon is not None and distance is not None:
            self.serializer_class = CounterDistanceSerializer
            distance_object = DistanceObject(km=distance)
            point = Point(x=float(lat), y=float(lon), srid=4326)
            queryset = (
                queryset.annotate(dist=DistanceFunction("geom", point))
                .filter(dist__lte=distance_object)
                .order_by("dist")
            )

        return queryset


class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for observations.
    """

    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationSerializer

    def get_queryset(self):
        queryset = Observation.objects.all()

        counter = self.request.query_params.get("counter")
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")
        source = self.request.query_params.get("source")

        if counter is not None:
            queryset = queryset.filter(counter=counter)

        if start_time is not None:
            queryset = queryset.filter(datetime__gte=start_time)
        if end_time is not None:
            queryset = queryset.filter(datetime__lte=end_time)

        if source is not None:
            queryset = queryset.filter(source=source)

        return queryset.order_by("-datetime")


@dataclass
class ObservationData:
    id: int
    station_id: int
    name: str
    short_name: str
    time_window_start: datetime
    time_window_end: datetime
    measured_time: int
    value: str
    unit: str


@dataclass
class CountersWithObservations:
    data_updated_time: datetime | None
    stations: QuerySet[CounterWithLatestObservations]


def _group_counter_sensors_in_qs(queryset):
    counter_groups = []
    # Group counters (sensors) due to LEFT JOIN in query with sensors returning multiple
    for _k, g in groupby(queryset):
        counter_groups.append(list(g))

    counters = []
    # Merges multiple counter rows by putting "duplicate" sensor rows in sensor_values
    for sensors in counter_groups:
        counter = sensors[0]
        duration_delta = timedelta(
            seconds=getattr(counter, "phenomenondurationseconds", 0)
        )
        measured_time = getattr(counter, "measured_time")
        time_window_start = (measured_time - duration_delta) if measured_time else None
        counter.sensor_values = [
            ObservationData(
                id=sensor.id,
                station_id=sensor.id,
                name=getattr(sensor, "measurement_type"),
                short_name=getattr(sensor, "short_name"),
                time_window_start=time_window_start,
                time_window_end=measured_time,
                measured_time=measured_time,
                value=getattr(sensor, "value"),
                unit=getattr(sensor, "unit"),
            )
            for sensor in sensors
        ]
        counter.tms_number = counter.id
        counter.data_updated_time = counter.counter_updated_at
        counters.append(counter)
    return counters


class CountersWithLatestObservationsView(viewsets.ViewSet):
    pagination_class = None

    def list(self, request):
        # itertools.groupby() requires sorted iterable
        queryset = CounterWithLatestObservations.objects.all().order_by("id")
        counters = _group_counter_sensors_in_qs(queryset)

        latest_updated_at = getattr(
            Observation.objects.latest("datetime"),
            "datetime",
            None,
        )
        data = CountersWithObservations(
            data_updated_time=latest_updated_at, stations=counters
        )
        serializer = CounterDataSerializer(data)

        return Response(serializer.data)
