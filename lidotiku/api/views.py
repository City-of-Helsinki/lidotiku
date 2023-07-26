from .models import EcoCounterCounter, EcoCounterObservation
from rest_framework import viewsets
# from rest_framework import permissions
from .serializers import CounterSerializer, ObservationSerializer


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