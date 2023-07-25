from .models import EcoCounterCounter, EcoCounterObservation
from rest_framework import viewsets
# from rest_framework import permissions
from .serializers import CounterSerializer


class CounterViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = EcoCounterCounter.objects.all()
    serializer_class = CounterSerializer
    # permission_classes = [permissions.IsAuthenticated]