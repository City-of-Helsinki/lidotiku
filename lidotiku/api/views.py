from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Counter, Observation
from .serializers import CounterSerializer, ObservationSerializer, CounterDataSerializer
from .utils import generateSensorName, getSensorInfo


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
    station_id: int
    name: str
    short_name: str
    time_window_start: datetime
    time_window_end: datetime
    measured_time: int
    value: str
    unit: str

class CountersDataView(viewsets.ViewSet):

    def _get_observations_for_counters(self, queryset: QuerySet[Counter]):
        for counter in queryset:
            observation = counter.get_latest_observation()
            measurementTime = getattr(observation, 'datetime', None)
            durationDelta = timedelta(seconds=getattr(observation, 'phenomenondurationseconds', 0))
            timeWindowStart = (measurementTime - durationDelta) if measurementTime else None
            sensorName = generateSensorName(type=getattr(observation, 'typeofmeasurement', 'count'), duration=getattr(observation, 'phenomenondurationseconds', 3600))
            sensorInfo = getSensorInfo(sensorName)
            sensorValues = {
                'id': sensorInfo['id'],
                'stationId': getattr(observation, 'id', None),
                'name': sensorName,
                'shortName': sensorInfo['shortName'],
                'timeWindowStart': timeWindowStart,
                'timeWindowEnd': measurementTime,
                'measuredTime': measurementTime,
                'value': getattr(observation, 'value', None),
                'unit': sensorInfo['unit']
            }
            counter.tms_number = counter.id
            counter.data_updated_time = getattr(observation, 'datetime', None)
            counter.sensor_values: List[ObservationData] = [ObservationData(**sensor_values)]
        return queryset

    def list(self, request):
        queryset = Counter.objects.all()
        queryset = self._get_observations_for_counters(queryset)
        latest_updated_at = getattr(Observation.objects.filter(id__in=queryset.values_list('id')).latest('datetime'), 'datetime', None)
        data = CountersData(dataUpdatedTime=latest_updated_at, stations=queryset)
        serializer = CounterDataSerializer(data)
        
        return Response(serializer.data)
    
    CountersWithObservationsQueryset = QuerySet[Counter]

    

