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
            measurement_time = getattr(observation, 'datetime', None)
            duration_delta = timedelta(seconds=getattr(observation, 'phenomenondurationseconds', 0))
            time_window_start = (measurement_time - duration_delta) if measurement_time else None
            sensor_values = {
                'id': getattr(observation, 'id', None),
                'station_id': getattr(observation, 'id', None),
                'name': getattr(counter, 'name', None),
                'short_name': getattr(counter, 'name', None),
                'time_window_start': time_window_start,
                'time_window_end': measurement_time,
                'measured_time': measurement_time,
                'value': getattr(observation, 'value', None),
                'unit': getattr(observation, 'unit', '')
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

    

