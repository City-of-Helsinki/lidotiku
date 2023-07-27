from .models import EcoCounterCounter, EcoCounterObservation 
from rest_framework import serializers


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    properties = serializers.SerializerMethodField()

    class Meta:
        model = EcoCounterCounter
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
        model = EcoCounterObservation
        fields = ['id','direction','value','unit','typeofmeasurement','phenomenondurationseconds','vehicletype','datetime','source']

class SensorValueSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    stationId = serializers.IntegerField()
    name = serializers.CharField()
    shortName = serializers.CharField()
    timeWindowStart = serializers.DateTimeField()
    timeWindowEnd = serializers.DateTimeField()
    measuredTime = serializers.DateTimeField()
    value = serializers.IntegerField(allow_null=True)
    unit = serializers.CharField()

class StationsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tmsNumber = serializers.IntegerField()
    dataUpdatedTime = serializers.DateTimeField()
    sensorValues = SensorValueSerializer()

class StationDataSerializer(serializers.Serializer):
    dataUpdatedTime = serializers.DateTimeField()
    stations = StationsSerializer(many=True)
