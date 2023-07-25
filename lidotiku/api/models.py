from django.db import models

class EcoCounterObservation(models.Model):
    # class Meta:
    #     managed = False
        
    # ID alone is not primary key    
    id = models.IntegerField(primary_key=True)
    direction = models.CharField(max_length=255)
    value = models.IntegerField(blank=True)
    unit = models.CharField(max_length=255)
    typeofmeasurement = models.CharField(max_length=255)
    phenomenondurationseconds = models.IntegerField(blank=False)
    vehicletype = models.CharField(max_length=255) 
    datetime = models.DateTimeField(max_length=255)
    source = models.CharField(max_length=255)

class EcoCounterCounter(models.Model):
    # class Meta:
    #     managed = False

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    classifying = models.CharField(max_length=255)
    longitude = models.CharField(max_length=255)
    latitude = models.CharField(max_length=255)
    crs_epsg = models.IntegerField()
    source = models.CharField(max_length=255)
    geom = models.CharField(max_length=255)
    


