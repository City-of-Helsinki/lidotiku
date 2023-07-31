from .models import Counter, Observation
from rest_framework import serializers


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    class Meta:
        model = Counter
        fields = ['type', 'id', 'geometry', 'properties']
    

    def get_type(self, obj):
        return 'Feature'

    def get_geometry(self, obj):
        return {  
            'type': 'Point',  
            'coordinates': [obj.longitude, obj.latitude]
        }  
    
    def get_properties(self, obj):
        return {
            'id': obj.id,
            # in digitraffic API tmsNumber is sometimes the same as ID, sometimes not
            'tms_number': obj.id,
            'name': obj.name,
            'collection_status': '',
            'state': '',
            'data_updated_time': '',
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class ObservationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Observation
        fields = ['id','direction','value','unit','typeofmeasurement','phenomenondurationseconds','vehicletype','datetime','source']

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
