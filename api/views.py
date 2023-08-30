from itertools import groupby
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.db.models import Sum, Avg
from django.db.models.query import QuerySet
from django.db.models.functions import Trunc
from django.db.models.expressions import Value
from django.db import DatabaseError
from django.core.exceptions import SuspiciousOperation
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.gdal.error import GDALException
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.settings import api_settings
from rest_framework_csv.renderers import PaginatedCSVRenderer
from django_filters import rest_framework as filters

from .models import Counter, Observation, CounterWithLatestObservations
from .serializers import (
    CounterSerializer,
    CounterFilterValidationSerializer,
    CounterDistanceSerializer,
    CounterDataSerializer,
    ObservationSerializer,
    ObservationAggregateSerializer,
)
from .filters import CounterFilter, ObservationFilter, ObservationAggregateFilter
from .schemas import CounterSchema, ObservationAggregateSchema

# pylint: disable=no-member


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000


# pylint: disable-next=too-many-ancestors
class CounterViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoint for counters
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CounterFilter
    pagination_class = None
    serializer_class = CounterSerializer
    schema = CounterSchema(request_serializer=CounterFilterValidationSerializer)
    queryset = Counter.objects.all()

    def get_queryset(self):
        try:
            query_params = self.request.query_params
        except AttributeError:
            query_params = {}  # type: ignore

        if len(query_params) > 0:
            # Be aware that this is not a fact check, user can put any amount of
            # query params in the request.
            CounterFilterValidationSerializer(data=query_params).is_valid(
                raise_exception=True
            )

        latitude = query_params.get("latitude")
        longitude = query_params.get("longitude")
        distance = query_params.get("distance")

        queryset = self.queryset

        if all([latitude, longitude, distance]):
            self.serializer_class = CounterDistanceSerializer
            point = Point(
                x=float(longitude), y=float(latitude), srid=4326  # type: ignore
            )
            queryset = self.queryset.annotate(distance=DistanceFunction("geom", point))
            if "order" not in query_params:
                queryset = queryset.order_by("distance")
        return queryset

    def create(self, request, *args, **kwargs):
        geojson_data = request.data.get("geometry")
        if not geojson_data:
            return Response({"error": "Missing `geometry` key in body."}, status=400)
        try:
            geometry = GEOSGeometry(str(geojson_data))
            counters = Counter.objects.filter(geom__intersects=geometry)
            serializer = self.get_serializer(counters, many=True)
            return Response(serializer.data, status=200)
        except (TypeError, ValueError) as error:
            return Response({"error": f"Invalid GeoJSON data: {error}"}, status=400)
        except (
            GEOSException,
            GDALException,
            DatabaseError,
            SuspiciousOperation,
        ):
            return Response({"error": "Unable to process the request."}, status=500)


class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for observations.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationFilter
    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationSerializer
    queryset = Observation.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        try:  # Try-except required for schema generation to work with django-filter
            filter_params = self.request.GET.copy()
            if "order" not in filter_params:
                queryset = queryset.order_by("datetime")
        except AttributeError:
            pass
        return queryset


class ObservationAggregateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for observations aggregation.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationAggregateFilter
    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationAggregateSerializer
    queryset = Observation.objects.all()
    schema = ObservationAggregateSchema()

    def get_queryset(self):
        try:  # Try-except required for schema generation to work with django-filter
            period = self.request.query_params.get("period")
        except AttributeError:
            period = None
        try:  # Try-except required for schema generation to work with django-filter
            measurement_type = self.request.query_params.get("measurement_type")
        except AttributeError:
            measurement_type = None

        if measurement_type == "speed":
            aggregation_calc: Avg | Sum = Avg("value")
        else:  # measurement_type == "count"
            aggregation_calc = Sum("value")
        queryset = (
            self.queryset.values("typeofmeasurement", "source")
            .annotate(start_time=Trunc("datetime", kind=period))
            .values(
                "start_time",
                "counter_id",
                "direction",
                "unit",
            )
            .annotate(aggregated_value=aggregation_calc)
            .annotate(period=Value(period))
        )
        try:  # Try-except required for schema generation to work with django-filter
            filter_params = self.request.GET.copy()
            if "order" not in filter_params:
                queryset = queryset.order_by("start_time")
        except AttributeError:
            pass
        return queryset


@dataclass
class ObservationData:  # pylint: disable=too-many-instance-attributes
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
    # Remove CSV renderer as it does not work well with nested values
    renderer_classes = tuple(
        filter(
            (lambda r: r != PaginatedCSVRenderer),  # type: ignore[arg-type]
            api_settings.DEFAULT_RENDERER_CLASSES,
        )
    )

    def list(self, _request):
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
