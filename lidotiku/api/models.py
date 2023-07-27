from django.db import models

class EcoCounterObservation(models.Model):
    class Meta:
        managed = False
        db_table = 'vw_observations'
    
    # ID alone is not primary key    
    id = models.BigIntegerField(primary_key=True)
    direction = models.CharField(max_length=32)
    value = models.BigIntegerField(blank=True)
    unit = models.CharField(max_length=8)
    typeofmeasurement = models.CharField(max_length=32)
    phenomenondurationseconds = models.BigIntegerField(blank=False)
    vehicletype = models.CharField(max_length=32) 
    datetime = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=32)

class EcoCounterCounter(models.Model):
    class Meta:
        managed = False
        db_table = 'vw_counters'

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    classifying = models.BooleanField()
    longitude = models.FloatField()
    latitude = models.FloatField()
    crs_epsg = models.BigIntegerField()
    source = models.CharField(max_length=32)
    geom = models.CharField(max_length=255) # TODO: convert later to correct type
    
    def get_latest_observation(self):
        if EcoCounterObservation.objects.filter(id=self.id).exists():
            latest_observation = EcoCounterObservation.objects.filter(id=self.id).latest('datetime')
        else:
            latest_observation = EcoCounterObservation.objects.none()
        return latest_observation
