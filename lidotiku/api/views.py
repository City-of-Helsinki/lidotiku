from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Counter, Observation
from .serializers import CounterSerializer, ObservationSerializer, CounterDataSerializer


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
class CountersData:
    def __init__(self, dataUpdatedTime, stations):
        self.dataUpdatedTime = dataUpdatedTime
        self.stations = stations

@dataclass
class ObservationData:
    id: int
    stationId: int
    name: str
    shortName: str
    timeWindowStart: datetime
    timeWindowEnd: datetime
    measuredTime: int
    value: str
    unit: str

class CountersDataView(viewsets.ViewSet):

    def _get_observations_for_counters(self, queryset: QuerySet[Counter]):
        for counter in queryset:
            observation = counter.get_latest_observation()
            measurementTime = getattr(observation, 'datetime', None)
            durationDelta = timedelta(seconds=getattr(observation, 'phenomenondurationseconds', 0))
            timeWindowStart = (measurementTime - durationDelta) if measurementTime else None
            sensorValues = {
                'id': getattr(observation, 'id', None),
                'stationId': getattr(observation, 'id', None),
                'name': getattr(counter, 'name', None),
                'shortName': getattr(counter, 'name', None),
                'timeWindowStart': timeWindowStart,
                'timeWindowEnd': measurementTime,
                'measuredTime': measurementTime,
                'value': getattr(observation, 'value', None),
                'unit': getattr(observation, 'unit', '')
            }
            counter.tmsNumber = counter.id
            counter.dataUpdatedTime = getattr(observation, 'datetime', None)
            counter.sensorValues: List[ObservationData] = [ObservationData(**sensorValues)]
        return queryset

    def list(self, request):
        queryset = Counter.objects.all()
        queryset = self._prepare_data_for_qs(queryset)
        latestUpdatedAt = getattr(Observation.objects.filter(id__in=queryset.values_list('id')).latest('datetime'), 'datetime', None)
        data = CountersData(dataUpdatedTime=latestUpdatedAt, stations=queryset)
        serializer = CounterDataSerializer(data)
        
        return Response(serializer.data)
    
    CountersWithObservationsQueryset = QuerySet[Counter]

    

