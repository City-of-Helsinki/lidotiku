# pylint: disable=abstract-method
from rest_framework import serializers
from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError
from .models import Counter, Observation


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
        distance: Distance = getattr(obj, "distance", None)
        return getattr(distance, "km", None)


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


class ObservationSerializer(serializers.HyperlinkedModelSerializer, ReadOnlySerializer):
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


class ObservationFilterSerializer(ReadOnlySerializer):
    counter = serializers.ListField(required=False, child=serializers.IntegerField())
    start_time = serializers.CharField(required=False)
    end_time = serializers.CharField(required=False)
    # pylint: disable=protected-access, no-member
    source = serializers.ModelField(
        Observation()._meta.get_field("source"),
        required=False,
    )
    measurement_type = serializers.CharField(required=False)
    vehicle_type = serializers.CharField(required=False)
    order = serializers.ChoiceField(choices=["asc", "desc"], required=False)


class ObservationAggregatedSerializer(
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


class ObservationAggregationFilterSerializer(ObservationFilterSerializer):
    period = serializers.CharField(required=False)

    def validate(self, attrs):
        counter = attrs.get("counter")
        aggregation = {
            "period": attrs.get("period"),
            "measurement_type": attrs.get("measurement_type"),
            "counter": counter,
        }
        valid_aggregates = ["hour", "day", "month", "year"]
        valid_measurement_types = ["speed", "count"]
        validation_errors = {}

        if (
            aggregation.get("period")
            and aggregation.get("period") not in valid_aggregates
        ):
            validation_errors[
                "period"
            ] = f"`{aggregation.get('period')}` not one of {valid_aggregates}"
        # When doing aggregation ensure required query params are set
        if aggregation.get("period") and not all(aggregation.values()):
            missing = [key for key, value in aggregation.items() if not value]
            validation_errors[
                "aggregate_combination"
            ] = f"Missing {missing} in aggregation request."

        if aggregation.get("measurement_type") not in valid_measurement_types:
            validation_errors[
                "measurement_type"
            ] = f"`{aggregation.get('measurement_type')}` not one of {valid_measurement_types}"
        if validation_errors:
            raise ValidationError(validation_errors)

        return attrs


class SensorSerializer(ReadOnlySerializer):
    id = serializers.IntegerField()
    station_id = serializers.IntegerField()
    name = serializers.CharField()
    short_name = serializers.CharField()
    time_window_start = serializers.DateTimeField()
    time_window_end = serializers.DateTimeField()
    measured_time = serializers.DateTimeField()
    value = serializers.IntegerField(allow_null=True)
    unit = serializers.CharField()


class CountersValuesSerializer(ReadOnlySerializer):
    id = serializers.IntegerField()
    tms_number = serializers.IntegerField()
    data_updated_time = serializers.DateTimeField()
    sensor_values = SensorSerializer(many=True)


class CounterDataSerializer(ReadOnlySerializer):
    data_updated_time = serializers.DateTimeField()
    stations = CountersValuesSerializer(many=True)
