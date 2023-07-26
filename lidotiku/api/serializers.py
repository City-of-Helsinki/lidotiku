from .models import EcoCounterCounter, EcoCounterObservation 
from rest_framework import serializers


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EcoCounterCounter
        fields = ['id', 'name', 'classifying','longitude','latitude','crs_epsg','source','geom']


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
