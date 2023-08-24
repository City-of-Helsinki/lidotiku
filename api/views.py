from itertools import groupby
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import cast
from django.db.models import Sum, Avg
from django.db.models.query import QuerySet
from django.db.models.functions import Trunc
from django.db.models.expressions import Value
from django.db import DatabaseError
from django.core.exceptions import SuspiciousOperation, RequestAborted
from django.contrib.gis.geos import Point, GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.measure import Distance as DistanceObject
from django.contrib.gis.gdal.error import GDALException
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import ChoiceField

from .models import Counter, Observation, CounterWithLatestObservations
from .serializers import (
    CounterSerializer,
    CounterFilterValidationSerializer,
    CounterDistanceSerializer,
    CounterDataSerializer,
    ObservationSerializer,
    ObservationFilterSerializer,
    ObservationAggregatedSerializer,
    ObservationAggregationFilterSerializer,
)
from .schemas import CounterSchema, ObservationSchema, ObservationAggregationSchema


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000


class CounterViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    API endpoint for counters
    """

    pagination_class = None
    serializer_class = CounterSerializer
    schema = CounterSchema(request_serializer=CounterFilterValidationSerializer)

    def get_queryset(self):
        queryset = Counter.objects.all()

        if len(self.request.query_params) > 0:
            CounterFilterValidationSerializer(data=self.request.query_params).is_valid(
                raise_exception=True
            )

        latitude = self.request.query_params.get("latitude")
        longitude = self.request.query_params.get("longitude")
        distance = self.request.query_params.get("distance")

        if all([latitude, longitude, distance]):
            self.serializer_class = CounterDistanceSerializer
            distance_object = DistanceObject(km=distance)
            point = Point(
                x=float(latitude), y=float(longitude), srid=4326  # type: ignore
            )
            queryset = (
                queryset.annotate(distance=DistanceFunction("geom", point))
                .filter(distance__lte=distance_object)
                .order_by("distance")
            )

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            geojson_data = request.data.get("geometry")
            if geojson_data:
                geometry = GEOSGeometry(str(geojson_data))
                counters = Counter.objects.filter(geom__intersects=geometry)
                serializer = self.get_serializer(counters, many=True)
                return Response(serializer.data, status=200)

            return Response({"error": "Invalid GeoJSON data"}, status=400)
        except (TypeError, ValueError) as error:
            return Response({"error": f"Invalid GeoJSON data: {error}"}, status=400)
        except (
            GEOSException,
            GDALException,
            DatabaseError,
            SuspiciousOperation,
            RequestAborted,
        ) as error:
            return Response(
                {"error": f"Unable to process request: {error}"}, status=500
            )


class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for observations.
    """

    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationSerializer
    schema = ObservationSchema(request_serializer=ObservationFilterSerializer)

    def get_queryset(self):
        ObservationFilterSerializer(data=self.request.query_params).is_valid(
            raise_exception=True
        )

        queryset = Observation.objects.all()
        counter: list[str] = self.request.query_params.getlist("counter")
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")
        source = self.request.query_params.get("source")
        measurement_type = self.request.query_params.get("measurement_type")
        order = self.request.query_params.get("order")

        if len(counter) > 0:
            queryset = queryset.filter(counter__in=counter)

        if start_time is not None:
            queryset = queryset.filter(datetime__gte=start_time)
        if end_time is not None:
            queryset = queryset.filter(datetime__lte=end_time)

        if source is not None:
            queryset = queryset.filter(source=source)

        if measurement_type is not None:
            queryset = queryset.filter(typeofmeasurement=measurement_type)

        if (
            order is not None
            and order
            in cast(
                ChoiceField,
                ObservationFilterSerializer().fields.get("order"),
            ).choices.keys()
            and order == "desc"
        ):
            queryset = queryset.order_by("-datetime")
        else:
            queryset = queryset.order_by("datetime")

        return queryset


class ObservationAggregationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for observations aggregation.
    """

    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationAggregatedSerializer
    schema = ObservationAggregationSchema(
        request_serializer=ObservationAggregationFilterSerializer
    )

    def get_queryset(self):
        ObservationAggregationFilterSerializer(data=self.request.query_params).is_valid(
            raise_exception=True
        )

        queryset = Observation.objects.all()
        counter = self.request.query_params.get("counter")
        start_time = self.request.query_params.get("start_time")
        end_time = self.request.query_params.get("end_time")
        aggregation = {
            "period": self.request.query_params.get("period"),
            "measurement_type": self.request.query_params.get("measurement_type"),
        }
        measurement_type = aggregation.get("measurement_type")
        order = self.request.query_params.get("order")

        if all(aggregation.values()) and counter is not None:
            queryset = queryset.filter(counter=counter)

            if start_time is not None:
                queryset = queryset.filter(datetime__gte=start_time)
            if end_time is not None:
                queryset = queryset.filter(datetime__lte=end_time)

            aggregation_period = aggregation.get("period")
            if measurement_type == "speed":
                aggregation_calc: Avg | Sum = Avg("value")
            else:  # measurement_type == "count"
                aggregation_calc = Sum("value")

            queryset = (
                queryset.filter(typeofmeasurement=measurement_type)  # type: ignore
                .values("typeofmeasurement", "source")
                .annotate(start_time=Trunc("datetime", kind=aggregation_period))
                .values(
                    "start_time",
                    "counter_id",
                    "direction",
                    "unit",
                )
                .annotate(aggregated_value=aggregation_calc)
                .annotate(period=Value(aggregation_period))
                .order_by("start_time")
            )
            if (
                order is not None
                and order
                in cast(
                    ChoiceField,
                    ObservationAggregationFilterSerializer().fields.get("order"),
                ).choices.keys()
                and order == "desc"
            ):
                queryset = queryset.order_by("-start_time")
            else:
                queryset = queryset.order_by("start_time")
            return queryset

        # Validation should raise ValidationError, so this is not expected to be returned.
        return queryset.none()


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
