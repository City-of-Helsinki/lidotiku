from datetime import datetime
from dataclasses import dataclass
from django.db.models import Sum, Avg
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
from django_filters import rest_framework as filters

from .models import Counter, Observation
from .serializers import (
    CounterFeatureCollectionSerializer,
    CounterFilterValidationSerializer,
    CounterDistanceSerializer,
    ObservationSerializer,
    ObservationAggregateSerializer,
)
from .filters import CounterFilter, ObservationFilter, ObservationAggregateFilter
from .schemas import CounterSchema, ObservationSchema, ObservationAggregateSchema

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
    Lists measurement devices or sensors which produce observational data.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CounterFilter
    pagination_class = None
    serializer_class = CounterFeatureCollectionSerializer
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = {"type": "FeatureCollection", "features": []}
        features: list = data.get("features", [])
        for counter in queryset:
            features.append(
                {
                    "type": "Feature",
                    "id": counter.id,
                    "geometry": counter.geom or None,
                    "properties": {
                        "id": getattr(counter, "id", None),
                        "name": getattr(counter, "name", ""),
                        "source": getattr(counter, "source", ""),
                        "crs_epsg": getattr(counter, "crs_epsg", ""),
                    },
                }
            )

        serializer = self.get_serializer(data=data)
        return Response(serializer.initial_data)

    def create(self, request, *args, **kwargs):
        """
        Lists counters within the given GeoJSON polygon area.
        """
        geojson_data = request.data
        if not geojson_data:
            return Response(
                {"error": "Missing GeoJSON polygon in the body."},
                status=400,
            )
        try:
            geometry = GEOSGeometry(str(geojson_data))
            counters = Counter.objects.filter(geom__intersects=geometry)
            serializer = self.get_serializer(counters, many=True)
            return Response(serializer.data, status=200)
        except (
            TypeError,
            ValueError,
            GEOSException,
            GDALException,
        ) as error:
            return Response({"error": f"Invalid GeoJSON data: {error}"}, status=400)
        except (
            DatabaseError,
            SuspiciousOperation,
        ):
            return Response({"error": "Unable to process the request."}, status=500)

    # pylint: disable-next=useless-parent-delegation
    def retrieve(self, request, *args, **kwargs):
        """
        Returns the information of a counter with the given identifier.
        """
        # The comment above is used to define a description for apidocs.
        return super().retrieve(request, *args, **kwargs)


class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns a paged and sorted list of observations produced by counters,
    matching the given search criteria.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationFilter
    pagination_class = LargeResultsSetPagination
    serializer_class = ObservationSerializer
    schema = ObservationSchema()
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
    Returns a paged and sorted list of the observational data,
    aggregated over the given period and matching the search criteria.
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
