from dataclasses import dataclass
from datetime import datetime

from django.contrib.gis.db.models.functions import Distance as DistanceFunction
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.geos.error import GEOSException
from django.core.exceptions import FieldError, SuspiciousOperation
from django.db import DatabaseError
from django.db.models import Avg, F, Sum
from django.db.models.expressions import Value
from django.db.models.functions import Trunc
from django_filters import rest_framework as filters
from djangorestframework_camel_case.render import (
    CamelCaseBrowsableAPIRenderer,
    CamelCaseJSONRenderer,
)
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework_csv.renderers import CSVRenderer

from .filters import (
    CounterFilter,
    DatasourceFilter,
    ObservationAggregateFilter,
    ObservationFilter,
)
from .models import Counter, Datasource, Observation
from .paginators import (
    LargeResultsSetPagination,
    ObservationsCursorPagination,
    SmallResultsSetPagination,
)
from .renderers import FeaturesPaginatedCSVRenderer
from .schemas import (
    CounterSchema,
    DatasourceSchema,
    ObservationAggregateSchema,
    ObservationSchema,
)
from .serializers import (
    CounterDistanceSerializer,
    CounterFilterValidationSerializer,
    CounterSerializer,
    DatasourceSerializer,
    ObservationAggregateSerializer,
    ObservationSerializer,
)


# pylint: disable=no-member
# Selects CSVRenderer explicitly for CSV retrieve action
# instead of deferring to defaults because Django selects
# unsupported PaginatedCSVRenderer
class BaseCSVRetrieveViewSet(viewsets.GenericViewSet):
    def get_renderers(self):
        format = self.request.query_params.get("format")
        if format == "csv" and self.action == "retrieve":
            return [CSVRenderer()]
        else:
            return super().get_renderers()


# pylint: disable-next=too-many-ancestors
class CounterViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    BaseCSVRetrieveViewSet,
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
    # Defining renderers explicitly to replace default PaginatedCSVRenderer
    # with FeaturesPaginatedCSVRenderer which maps the data from features object
    renderer_classes = [
        CamelCaseJSONRenderer,
        CamelCaseBrowsableAPIRenderer,
        FeaturesPaginatedCSVRenderer,
    ]

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
                x=float(longitude),
                y=float(latitude),
                srid=4326,  # type: ignore
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
        queryset = super().get_queryset()
        try:  # Try-except required for schema generation to work with django-filter
            filter_params = self.request.GET.copy()
            if "order" not in filter_params:
                queryset = queryset.order_by("-datetime")
        except AttributeError:
            pass

        if "page" in self.request.query_params:
            self.pagination_class = LargeResultsSetPagination
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
                queryset = queryset.order_by("-start_time")
        except AttributeError:
            pass
        return queryset


class DatasourceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, BaseCSVRetrieveViewSet
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
            queryset = queryset.annotate(description=F(f"description_{language}"))
        except AttributeError:
            language = "en"
        except FieldError:
            raise ValidationError(
                detail={
                    "language": f"Select a valid choice. "
                    f"{language} is not one of the available choices."
                },
                code="invalid_choice",
            )
        return queryset.order_by("name")


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
