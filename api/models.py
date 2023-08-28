from django.db import models
from django.contrib.gis.db import models as gis_models


# pylint: disable=abstract-method,too-few-public-methods
class ReadOnlyModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        raise NotImplementedError(
            "This is a read-only model and does not support saving objects."
        )

    def create(self, *args, **kwargs):
        raise NotImplementedError(
            "This is a read-only model and does not support creating objects."
        )

    def update(self, *args, **kwargs):
        raise NotImplementedError(
            "This is a read-only model and does not support updating objects."
        )

    def delete(self, *args, **kwargs):
        raise NotImplementedError(
            "This is a read-only model and does not support deleting objects."
        )


class Counter(ReadOnlyModel):
    """Database View"""

    class Meta:
        managed = False
        db_table = '"lido"."vw_counters"'

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    classifying = models.BooleanField()
    longitude = models.FloatField()
    latitude = models.FloatField()
    crs_epsg = models.BigIntegerField()
    source = models.CharField(max_length=32)
    geom = gis_models.PointField()


class Observation(ReadOnlyModel):
    """Database View"""

    class Meta:
        managed = False
        db_table = '"lido"."vw_observations"'
        unique_together = ("id", "source")

    # id (ctid) is only unique within a source
    id = models.CharField(primary_key=True, db_column="ctid")
    counter = models.ForeignKey(Counter, db_column="id", on_delete=models.RESTRICT)
    direction = models.CharField(max_length=32)
    value = models.BigIntegerField(blank=True)
    unit = models.CharField(max_length=8)
    typeofmeasurement = models.CharField(max_length=32)
    phenomenondurationseconds = models.BigIntegerField(blank=False)
    vehicletype = models.CharField(max_length=32)
    datetime = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=32)


class CounterWithLatestObservations(ReadOnlyModel):
    """Database View"""

    class Meta:
        managed = False
        db_table = '"lido"."vw_counters_with_latest_sensor_observations"'

    id = models.BigIntegerField(primary_key=True)
    short_name = models.CharField(db_column="measurementtypeshortname")
    source = models.CharField()
    measurement_type = models.CharField(db_column="measurementtypename")
    measured_time = models.DateTimeField(db_column="datetime")
    phenomenondurationseconds = models.IntegerField()
    unit = models.CharField()
    value = models.IntegerField()
    counter_updated_at = models.DateField()
