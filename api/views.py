from itertools import groupby
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List
from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Counter, Observation, CounterWithLatestObservations
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
    def __init__(self, data_updated_time, stations):
        self.data_updated_time = data_updated_time
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


@dataclass
class CountersWithObservations:
    data_updated_time: datetime
    stations: QuerySet[CounterWithLatestObservations]


class CountersWithLatestObservationsView(viewsets.ViewSet):
    def list(self, request):
        # itertools.groupby() requires sorted iterable
        queryset = CounterWithLatestObservations.objects.all().order_by("id")
        counter_groups = []
        # Group counters (sensors) due to LEFT JOIN in query with sensors returning multiple
        for _k, g in groupby(queryset):
            counter_groups.append(list(g))

        counters = []
        # Merges multiple counter rows by putting "duplicate" sensor rows in sensor_values
        for sensors in counter_groups:
            counter = sensors[0]
            duration_delta = timedelta(
                seconds=getattr(counter, "phenomenondurationseconds", 0)
            )
            measured_time = getattr(counter, "measured_time")
            time_window_start = (
                (measured_time - duration_delta) if measured_time else None
            )
            counter.sensor_values: List[ObservationData] = [
                ObservationData(
                    id=sensor.id,
                    station_id=sensor.id,
                    name=getattr(sensor, "measurement_type"),
                    short_name=getattr(sensor, "short_name"),
                    time_window_start=time_window_start,
                    time_window_end=measured_time,
                    measured_time=measured_time,
                    value=getattr(sensor, "value"),
                    unit=getattr(sensor, "unit"),
                )
                for sensor in sensors
            ]
            counter.tms_number = counter.id
            counter.data_updated_time = counter.counter_updated_at
            counters.append(counter)

        latest_updated_at = getattr(
            Observation.objects.latest("datetime"),
            "datetime",
            None,
        )
        data = CountersWithObservations(
            data_updated_time=latest_updated_at, stations=counters
        )
        serializer = CounterDataSerializer(data)

        return Response(serializer.data)
