from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from .models import Counter, Datasource, Observation


# pylint: disable=abstract-method,too-few-public-methods
class ReadOnlySerializer(serializers.Serializer):
    class Meta:
        read_only_fields = "__all__"

    def create(self, _validated_data):
        raise NotImplementedError(
            "This is a read-only serializer and does not support updating objects."
        )

    def update(self, _instance, _validated_data):
        raise NotImplementedError(
            "This is a read-only serializer and does not support creating objects."
        )

    def save(self, **kwargs):
        raise NotImplementedError(
            "This is a read-only serializer and does not support saving objects."
        )


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Counter Feature Example",
            summary="Example counter as GeoJSON Feature",
            description="A counter represented as a GeoJSON Feature with "
            "geometry and properties",
            value={
                "type": "Feature",
                "id": 1,
                "geometry": {"type": "Point", "coordinates": [24.9414, 60.1699]},
                "properties": {
                    "id": 1,
                    "name": "Example Counter",
                    "source": "eco-counter",
                    "source_id": "123456",
                    "classifying": True,
                    "crs_epsg": 4326,
                    "municipality_code": "091",
                    "data_received": True,
                    "first_stored_observation": "2023-01-01T12:00:00Z",
                    "last_stored_observation": "2023-12-31T23:59:59Z",
                },
            },
        )
    ]
)
class CounterSerializer(serializers.HyperlinkedModelSerializer, ReadOnlySerializer):
    geometry = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()
    type = serializers.CharField(default="Feature")

    class Meta:
        model = Counter
        fields = ["type", "id", "geometry", "properties"]

    def get_geometry(self, obj):
        return {"type": "Point", "coordinates": [obj.geom.x, obj.geom.y]}

    def get_properties(self, obj):
        datetime_serializer = serializers.DateTimeField()
        return {
            "id": obj.id,
            "name": obj.name,
            "source": obj.source,
            "source_id": obj.source_id,
            "classifying": obj.classifying,
            "crs_epsg": obj.crs_epsg,
            # Municipality codes stored in database as integers
            # but correct format includes a leading zero
            "municipality_code": f"0{obj.municipality_code}",
            "data_received": obj.data_received,
            "first_stored_observation": datetime_serializer.to_representation(
                obj.first_stored_observation
            ),
            "last_stored_observation": datetime_serializer.to_representation(
                obj.last_stored_observation
            ),
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class CounterDistanceSerializer(CounterSerializer):
    distance = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    class Meta:
        model = Counter
        fields = ["id", "geometry", "distance", "properties"]

    def get_distance(self, obj):
        distance: Distance | None = getattr(obj, "distance", None)
        return getattr(distance, "km", None)

    def get_properties(self, obj):
        return {
            "id": obj.id,
            "name": obj.name,
            "source": obj.source,
            "classifying": obj.classifying,
            "crs_epsg": obj.crs_epsg,
            "distance": self.get_distance(obj),
        }


class CounterFilterValidationSerializer(serializers.Serializer):
    longitude = serializers.FloatField(required=False)
    latitude = serializers.FloatField(required=False)
    distance = serializers.FloatField(required=False)

    def validate(self, attrs):
        longitude = attrs.get("longitude")
        latitude = attrs.get("latitude")
        distance = attrs.get("distance")

        coordinate_parameters = {
            "latitude": latitude,
            "longitude": longitude,
            "distance": distance,
        }

        validation_errors = {}
        none_values = [x is not None for x in coordinate_parameters.values()]
        if any(none_values) and not all(none_values):
            missing_params = [
                key for key, value in coordinate_parameters.items() if value is None
            ]
            validation_errors["Missing parameters"] = (
                "Missing query argument(s): "
                + f"{', '.join(missing_params)}. "
                + "Latitude, longitude and distance must all be provided."
            )

        if validation_errors:
            raise ValidationError(validation_errors)

        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Observation Example",
            summary="Example observation measurement",
            description="A single observation measurement from a counter",
            value={
                "typeofmeasurement": "count",
                "phenomenondurationseconds": 3600,
                "vehicletype": "bicycle",
                "direction": "in",
                "unit": "count",
                "value": 25,
                "datetime": "2023-01-01T12:00:00Z",
                "source": "eco-counter",
                "counter": "https://example.com/api/counters/1/",
                "counter_id": 1,
            },
        )
    ]
)
class ObservationSerializer(serializers.HyperlinkedModelSerializer, ReadOnlySerializer):
    datetime = serializers.DateTimeField()

    class Meta:
        model = Observation
        fields = [
            "typeofmeasurement",
            "phenomenondurationseconds",
            "vehicletype",
            "direction",
            "unit",
            "value",
            "datetime",
            "source",
            "counter",
            "counter_id",
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Observation Aggregate Example",
            summary="Example aggregated observation data",
            description="Observation data aggregated over a time period",
            value={
                "period": "hour",
                "counter_id": 1,
                "start_time": "2023-01-01T12:00:00Z",
                "direction": "in",
                "unit": "count",
                "aggregated_value": 150,
            },
        )
    ]
)
class ObservationAggregateSerializer(
    serializers.HyperlinkedModelSerializer, ReadOnlySerializer
):
    start_time = serializers.DateTimeField()
    aggregated_value = serializers.SerializerMethodField()
    period = serializers.CharField()
    unit = serializers.CharField()

    class Meta:
        model = Observation
        fields = [
            "period",
            "counter_id",
            "start_time",
            "direction",
            "unit",
            "aggregated_value",
        ]

    def get_aggregated_value(self, obj):
        return obj.get("aggregated_value")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Datasource Example",
            summary="Example data source information",
            description="Information about a traffic data source",
            value={
                "name": "eco-counter",
                "license": "Creative Commons",
                "description": "Eco-Counter provides bicycle and "
                "pedestrian counting data",
            },
        )
    ]
)
class DatasourceSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    license = serializers.CharField()
    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        return getattr(obj, "description", None)

    class Meta:
        model = Datasource
        fields = [
            "name",
            "license",
            "description",
        ]


class GeoJSONPolygonSerializer(serializers.Serializer):
    """Serializer for GeoJSON Polygon used in POST requests to filter counters."""

    type = serializers.ChoiceField(choices=["Polygon"])
    coordinates = serializers.ListField(
        child=serializers.ListField(
            child=serializers.ListField(child=serializers.FloatField(), min_length=2),
            min_length=4,
        )
    )
    bbox = serializers.ListField(
        child=serializers.FloatField(), min_length=4, required=False
    )
