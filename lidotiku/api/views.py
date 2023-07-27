from datetime import datetime
from .models import Counter, Observation
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import CounterSerializer, ObservationSerializer, StationDataSerializer, StationsSerializer


class CounterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for counters/sensors.
    """
    queryset = Counter.objects.all()
    serializer_class = CounterSerializer
    # permission_classes = [permissions.IsAuthenticated]

class ObservationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for observations.
    """
    queryset = Observation.objects.all()[:999]
    serializer_class = ObservationSerializer
    # permission_classes = [permissions.IsAuthenticated]
class StationsData:
    def __init__(self, dataUpdatedTime, stations):
        self.dataUpdatedTime = dataUpdatedTime
        self.stations = stations

class Observation:
    now = datetime.now() # TODO: Replace with some value from somewhere
    def __init__(self, observation):
        self.id = getattr(observation, 'id', None)
        self.stationId = getattr(observation, 'id', None)
        self.name = 'name'
        self.shortName = getattr(observation, 'unit', None)
        self.timeWindowStart = getattr(observation, 'datetime', None)
        self.timeWindowEnd = getattr(observation, 'datetime', None)
        self.measuredTime = getattr(observation, 'datetime', None)
        self.value = getattr(observation, 'value', None)
        self.unit = getattr(observation, 'unit', '')

class StationsDataView(viewsets.ViewSet):

    def list(self, request):
        now = datetime.now()
        queryset = Counter.objects.all()
        for counter in queryset:
            counter.tmsNumber = counter.id
            counter.dataUpdatedTime = now
            counter.sensorValues = Observation(counter.get_latest_observation())
        data = StationsData(dataUpdatedTime=now, stations=queryset)
        serializer = StationDataSerializer(data)
        
        return Response(serializer.data)
