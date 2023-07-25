from .models import EcoCounterCounter, EcoCounterObservation 
from rest_framework import serializers


class CounterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EcoCounterCounter
        fields = ['id', 'name', 'classifying','longitude','latitude','crs_epsg','source','geom']