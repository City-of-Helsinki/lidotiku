from rest_framework import serializers
from django.contrib.gis.db.models.functions import Distance
from django.core.exceptions import ValidationError
from .models import Counter, Observation


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    geometry = serializers.SerializerMethodField()

    class Meta:
        model = Counter
        fields = ["id", "name", "classifying", "crs_epsg", "source", "geometry"]

    def get_geometry(self, obj):
        return {"type": "Point", "coordinates": [obj.geom.x, obj.geom.y]}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class CounterDistanceSerializer(CounterSerializer):
    distance = serializers.SerializerMethodField()

    class Meta:
        model = Counter
        fields = [
            "id",
            "name",
            "classifying",
            "crs_epsg",
            "source",
            "geometry",
            "distance",
        ]

    def get_distance(self, obj):
        try:
            distance: Distance = getattr(obj, "distance")
            return distance.km
        except AttributeError:
            return None


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

        if any(coordinate_parameters.values()) and not all(
            coordinate_parameters.values()
        ):
            missing_params = [
                key for key, value in coordinate_parameters.items() if value is None
            ]
            validation_errors[
                "Missing parameters"
            ] = f"Missing query argument(s): {', '.join(missing_params)}. Latitude, longitude and distance must all be provided"

        if validation_errors:
            raise ValidationError(validation_errors)

        return attrs


class ObservationSerializer(serializers.HyperlinkedModelSerializer):
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


class SensorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    station_id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    time_window_start = serializers.DateTimeField(read_only=True)
    time_window_end = serializers.DateTimeField(read_only=True)
    measured_time = serializers.DateTimeField(read_only=True)
    value = serializers.IntegerField(read_only=True, allow_null=True)
    unit = serializers.CharField(read_only=True)


class CountersValuesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tms_number = serializers.IntegerField(read_only=True)
    data_updated_time = serializers.DateTimeField(read_only=True)
    sensor_values = SensorSerializer(read_only=True, many=True)


class CounterDataSerializer(serializers.Serializer):
    data_updated_time = serializers.DateTimeField(read_only=True)
    stations = CountersValuesSerializer(read_only=True, many=True)
