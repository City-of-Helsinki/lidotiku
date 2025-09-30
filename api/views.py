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
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
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
from .serializers import (
    CounterDistanceSerializer,
    CounterFilterValidationSerializer,
    CounterSerializer,
    DatasourceSerializer,
    GeoJSONPolygonSerializer,
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


def get_source_choices():
    """Get available source values from the database"""
    try:
        return list(
            Datasource.objects.values_list("name", flat=True)
            .distinct()
            .order_by("name")
        )
    except RuntimeError:
        return []  # Return empty list if DB not available (e.g., during tests)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="municipality_code",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Finnish municipality code of counter location "
                "(e.g. 091 for Helsinki, 092 for Vantaa, and 049 for Espoo), "
                "leading zero is optional. "
                "See further [Kuntanumero](https://fi.wikipedia.org/wiki/Kuntanumero).",
                explode=False,
            ),
            OpenApiParameter(
                name="source",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Data source.",
                explode=False,
                enum=get_source_choices(),
            ),
            OpenApiParameter(
                name="format",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Output format. Default is JSON. Use `format=csv` "
                "for CSV format.",
                explode=False,
                enum=["json", "csv", "api"],
            ),
            OpenApiParameter(
                name="latitude",
                type=float,
                location=OpenApiParameter.QUERY,
                description="Latitude coordinate for distance-based filtering.",
                explode=False,
            ),
            OpenApiParameter(
                name="longitude",
                type=float,
                location=OpenApiParameter.QUERY,
                description="Longitude coordinate for distance-based filtering.",
                explode=False,
            ),
            OpenApiParameter(
                name="distance",
                type=float,
                location=OpenApiParameter.QUERY,
                description="Distance in kilometers for filtering "
                "counters near coordinates.",
                explode=False,
            ),
        ],
    ),
    create=extend_schema(
        request=GeoJSONPolygonSerializer,
        examples=[
            OpenApiExample(
                "GeoJSON Polygon Example",
                summary="Query with GeoJSON Polygon",
                description="Use this GeoJSON polygon to filter counters "
                "within the specified area",
                value={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [24.5, 60.2],
                            [24.5, 60.9],
                            [24.8, 60.9],
                            [24.8, 60.2],
                            [24.5, 60.2],
                        ]
                    ],
                },
            )
        ],
    ),
    retrieve=extend_schema(),
)
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="counter",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter observations by counter ID.",
                explode=False,
            ),
            OpenApiParameter(
                name="datetime_after",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter observations after this datetime "
                "(ISO 8601 format).",
                explode=False,
            ),
            OpenApiParameter(
                name="datetime_before",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter observations before this datetime "
                "(ISO 8601 format).",
                explode=False,
            ),
            OpenApiParameter(
                name="source",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by data source.",
                explode=False,
            ),
            OpenApiParameter(
                name="order",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Order results by field. "
                "Use '-' prefix for descending order.",
                explode=False,
            ),
        ],
    )
)
class ObservationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Returns a paged and sorted list of observations produced by counters,
    matching the given search criteria.
    """

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ObservationFilter
    pagination_class = ObservationsCursorPagination
    serializer_class = ObservationSerializer
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="counter",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter observations by counter ID.",
                explode=False,
            ),
            OpenApiParameter(
                name="datetime_after",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter observations after this datetime "
                "(ISO 8601 format).",
                explode=False,
            ),
            OpenApiParameter(
                name="datetime_before",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter observations before this datetime "
                "(ISO 8601 format).",
                explode=False,
            ),
            OpenApiParameter(
                name="period",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Aggregation period (hour, day, week, month, year).",
                explode=False,
                enum=["hour", "day", "week", "month", "year"],
            ),
            OpenApiParameter(
                name="measurement_type",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Type of measurement for aggregation (count or speed).",
                explode=False,
                enum=["count", "speed"],
            ),
            OpenApiParameter(
                name="source",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by data source.",
                explode=False,
            ),
            OpenApiParameter(
                name="order",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Order results by field. Use '-' prefix for "
                "descending order.",
                explode=False,
            ),
        ],
    )
)
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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name="language",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Language for localized description (e.g., "
                "'en', 'fi', 'sv').",
                explode=False,
                enum=["en", "fi", "sv"],
            ),
            OpenApiParameter(
                name="format",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Output format. Default is JSON. Use `format=csv` "
                "for CSV format.",
                explode=False,
                enum=["json", "csv", "api"],
            ),
        ],
    ),
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="language",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Language for localized description (e.g., "
                "'en', 'fi', 'sv').",
                explode=False,
                enum=["en", "fi", "sv"],
            ),
            OpenApiParameter(
                name="format",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Output format. Default is JSON. Use `format=csv` "
                "for CSV format.",
                explode=False,
                enum=["json", "csv", "api"],
            ),
        ],
    ),
)
class DatasourceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, BaseCSVRetrieveViewSet
):
    """
    Lists the traffic data sources for which counters and observations exist.
    """

    queryset = Datasource.objects.all()
    serializer_class = DatasourceSerializer
    filterset_class = DatasourceFilter
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
