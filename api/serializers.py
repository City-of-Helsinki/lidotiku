import pytz
from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Counter, Observation, Datasource


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
        return {
            "id": obj.id,
            "name": obj.name,
            "source": obj.source,
            "classifying": obj.classifying,
            "crs_epsg": obj.crs_epsg,
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
