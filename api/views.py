from dataclasses import dataclass
from datetime import datetime

from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.geos.error import GEOSException
from django.core.exceptions import SuspiciousOperation
from django.db import DatabaseError
from django.db.models import Avg, Sum, F
from django.db.models.expressions import Value
from django.db.models.functions import Trunc
from django_filters import rest_framework as filters
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.utils.urls import replace_query_param, remove_query_param

from .filters import (
    CounterFilter,
    ObservationAggregateFilter,
    ObservationFilter,
    DatasourceFilter,
)
from .models import Counter, Observation, Datasource
from .schemas import (
    CounterSchema,
    ObservationAggregateSchema,
    ObservationSchema,
    DatasourceSchema,
)
from .serializers import (
    CounterDistanceSerializer,
    CounterFilterValidationSerializer,
    CounterSerializer,
    ObservationAggregateSerializer,
    ObservationSerializer,
    DatasourceSerializer,
)
from .utils import counter_alias_map

# pylint: disable=no-member


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000

    def get_previous_link(self) -> str | None:
        previous_link = super().get_previous_link()
        if not self.page.has_previous():
            return None
        if self.page.previous_page_number() == 1:
            previous_link = replace_query_param(previous_link, self.page_query_param, 1)
        if "page" in self.request.query_params:
            previous_link = remove_query_param(previous_link, "cursor")
        return previous_link

    def get_next_link(self) -> str | None:
        if "page" in self.request.query_params:
            return remove_query_param(super().get_next_link(), "cursor")
        return super().get_next_link()


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000


class ObservationsCursorPagination(CursorPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    ordering = ["-datetime", "counter_id", "typeofmeasurement", "direction"]
    max_page_size = 10000

    def get_schema_operation_parameters(self, view: APIView) -> list:
        parameters = super().get_schema_operation_parameters(view)

        page_parameter = {
            "name": "page",
            "required": False,
            "in": "query",
            "description": "A page number within the paginated result set. If this parameter is set, it supercedes the cursor parameter and results will be returned as numbered pages.",
            "schema": {"type": "integer"},
        }

        parameters.append(page_parameter)
        return parameters


class ObservationAggregateCursorPagination(CursorPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    ordering = ["-start_time", "counter_id", "direction"]
    max_page_size = 10000

    def get_schema_operation_parameters(self, view: APIView) -> list:
        parameters = super().get_schema_operation_parameters(view)

        page_parameter = {
            "name": "page",
            "required": False,
            "in": "query",
            "description": "A page number within the paginated result set. If this parameter is set, it supercedes the cursor parameter and results will be returned as numbered pages.",
            "schema": {"type": "integer"},
        }

        parameters.append(page_parameter)
        return parameters


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
    pagination_class = SmallResultsSetPagination
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
            geometry = GEOSGeometry(str(geojson_data), srid=4326)
            counters = Counter.objects.filter(geom__within=geometry)
            serializer = self.get_serializer(counters, many=True)
            data = {"type": "FeatureCollection", "features": serializer.data}
            return Response(data, status=200)
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.paginate_queryset(queryset), many=True)
        paginated_response = self.get_paginated_response(serializer.data).data
        results = {"type": "FeatureCollection", "features": serializer.data}
        response_data = {**paginated_response, "results": results}
        return Response(response_data, status=200)


class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns a paged and sorted list of observations produced by counters,
    matching the given search criteria.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationFilter
    pagination_class = ObservationsCursorPagination
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

        if "page" in self.request.query_params:
            self.pagination_class = LargeResultsSetPagination

        elif "order" in self.request.query_params:
            fixed_orderings = ["typeofmeasurement", "direction"]

            order_params = self.request.query_params.get("order").split(",")
            # provided
            order_params = [
                counter_alias_map.get(param) if "counter" in param else param
                for param in order_params
            ]

            secondary_ordering = []
            if "counter" in order_params[0]:
                secondary_ordering = ["-datetime"]
            elif "datetime" in order_params[0]:
                secondary_ordering = ["counter_id"]
            self.pagination_class.ordering = (
                order_params + secondary_ordering + fixed_orderings
            )

        return queryset


class ObservationAggregateViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns a paged and sorted list of the observational data,
    aggregated over the given period and matching the search criteria.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationAggregateFilter
    pagination_class = ObservationAggregateCursorPagination
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

        if "page" in self.request.query_params:
            self.pagination_class = LargeResultsSetPagination

        elif "order" in self.request.query_params:
            self.pagination_class.ordering = [
                self.request.query_params.get("order"),
                "counter_id",
                "direction",
            ]

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


class DatasourcesViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    Lists the traffic data sources for which counters and observations exist.
    """

    queryset = Datasource.objects.all()
    serializer_class = DatasourceSerializer
    filterset_class = DatasourceFilter
    schema = DatasourceSchema()
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = None

    def get_queryset(self):
        queryset = self.queryset
        try:  # Try-except required for schema generation to work with django-filter
            language = self.request.query_params.get("language", "en")
        except AttributeError:
            language = "en"

        queryset = queryset.annotate(description=F(f"description_{language}"))
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
