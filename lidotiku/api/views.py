from datetime import datetime
from .models import EcoCounterCounter, EcoCounterObservation
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import CounterSerializer, ObservationSerializer, StationDataSerializer, StationsSerializer


class CounterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for counters/sensors.
    """
    queryset = EcoCounterCounter.objects.all()
    serializer_class = CounterSerializer
    # permission_classes = [permissions.IsAuthenticated]

class ObservationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for observations.
    """
    queryset = EcoCounterObservation.objects.all()[:999]
    serializer_class = ObservationSerializer
    # permission_classes = [permissions.IsAuthenticated]
class StationsData:
    def __init__(self, dataUpdatedTime, stations):
        self.dataUpdatedTime = dataUpdatedTime
        self.stations = stations

class Observation:
    now = datetime.now() # TODO: Replace with some value from somewhere
    def __init__(self, observation):
        self.id = observation.id or None
        self.stationId = observation.id or None
        self.name = 'name'
        self.shortName = observation.unit or None
        self.timeWindowStart = observation.datetime or None
        self.timeWindowEnd = observation.datetime or None
        self.measuredTime = observation.datetime or None
        self.value = observation.value or None
        self.unit = observation.unit or ''

class StationsDataView(viewsets.ViewSet):

    def list(self, request):
        now = datetime.now()
        queryset = EcoCounterCounter.objects.all()
        for counter in queryset:
            counter.tmsNumber = counter.id
            counter.dataUpdatedTime = now
            counter.sensorValues = Observation(counter.get_latest_observation())
        data = StationsData(dataUpdatedTime=now, stations=queryset)
        serializer = StationDataSerializer(data)
        
        return Response(serializer.data)
