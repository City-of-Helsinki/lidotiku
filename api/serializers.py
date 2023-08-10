from rest_framework import serializers
from .models import Counter, Observation


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    geometry = serializers.SerializerMethodField()

    class Meta:
        model = Counter
        fields = ["id", "name", "classifying", "crs_epsg", "source", "geometry"]

    def get_geometry(self, obj):
        return {"type": "Point", "coordinates": [obj.longitude, obj.latitude]}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


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
