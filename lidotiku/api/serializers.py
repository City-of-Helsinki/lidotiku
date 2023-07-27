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
        return "Feature"

    def get_geometry(self, obj):  
        return {  
            'type': 'Point',  
            'coordinates': [obj.longitude, obj.latitude]
        }  
    
    def get_properties(self, obj):
        return {
            'id': obj.id,
            # in digitraffic API tmsNumber is sometimes the same as ID, sometimes not
            'tmsNumber': obj.id,
            'name': obj.name,
            'collectionStatus': '',
            'state': '',
            'dataUpdatedTime' : ''
        }


    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class ObservationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Observation
        fields = ['id','direction','value','unit','typeofmeasurement','phenomenondurationseconds','vehicletype','datetime','source']

class SensorValuesSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    stationId = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    shortName = serializers.CharField(read_only=True)
    timeWindowStart = serializers.DateTimeField(read_only=True)
    timeWindowEnd = serializers.DateTimeField(read_only=True)
    measuredTime = serializers.DateTimeField(read_only=True)
    value = serializers.IntegerField(read_only=True, allow_null=True)
    unit = serializers.CharField(read_only=True)

class CountersValuesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tmsNumber = serializers.IntegerField(read_only=True)
    dataUpdatedTime = serializers.DateTimeField(read_only=True)
    sensorValues = SensorValuesSerializer(read_only=True)

class CounterDataSerializer(serializers.Serializer):
    dataUpdatedTime = serializers.DateTimeField(read_only=True)
    stations = CountersValuesSerializer(read_only=True, many=True)
