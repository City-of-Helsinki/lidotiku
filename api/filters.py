from datetime import datetime

from django.contrib.gis.measure import Distance as DistanceObject
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.timezone import make_aware
from django_filters.rest_framework import (
    BaseInFilter,
    CharFilter,
    ChoiceFilter,
    DateFilter,
    FilterSet,
    NumberFilter,
    OrderingFilter,
)
from django.db.models import F


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


class NumberMaxMinFilter(NumberFilter):
    def __init__(
        self,
        field_name=None,
        lookup_expr=None,
        *,
        label=None,
        method=None,
        distinct=False,
        exclude=False,
        **kwargs,
    ):
        super().__init__(
            field_name=None,
            lookup_expr=None,
            label=None,
            method=None,
            distinct=False,
            exclude=False,
            **kwargs,
        )
        min_value = kwargs.get("min_value")
        max_value = kwargs.get("max_value")
        if min_value is not None:
            self.min_value = min_value
        if max_value is not None:
            self.max_value = max_value

    def get_max_validator(self, max_value=1e50):
        return MaxValueValidator(max_value)

    def get_min_validator(self, min_value=-1e50):
        return MinValueValidator(min_value)

    @property
    def field(self):
        if not hasattr(self, "_field"):
            field = super().field
            max_validator = self.get_max_validator()
            min_validator = self.get_min_validator()
            if max_validator:
                field.validators.append(max_validator)
            if min_validator:
                field.validators.append(min_validator)
            # pylint: disable-next=attribute-defined-outside-init
            self._field = field
        return self._field


def filter_end_date(queryset, name, value):
    # Make end_date inclusive until end of day
    end_date = make_aware(datetime.combine(value, datetime.max.time()))
    return queryset.filter(**{f"{name}__lte": end_date})


class CounterFilter(FilterSet):
    latitude = NumberMaxMinFilter(label="Latitude", min_value=-90, max_value=90)
    longitude = NumberMaxMinFilter(label="Longitude", min_value=-180, max_value=180)
    distance = NumberFilter(
        method="distance_filter",
        label="Distance in kilometers, how far can a counter be from the defined point.",
    )
    source = CharFilter(field_name="source", lookup_expr="iexact", label="Data source.")
    municipality_code = NumberInFilter(
        field_name="municipality_code",
        lookup_expr="in",
        label="Finnish municipality code of counter location (e.g. 091 for Helsinki, 092 for Vantaa, and 049 for Espoo), leading zero is optional. See further [Kuntanumero](https://fi.wikipedia.org/wiki/Kuntanumero).",
    )

    def distance_filter(self, _queryset, _name, _value):
        query_params = self.request.query_params
        latitude = query_params.get("latitude")
        longitude = query_params.get("longitude")
        distance = query_params.get("distance")

        queryset = self.queryset
        if all([latitude, longitude, distance]):
            distance_object = DistanceObject(km=distance)
            queryset = queryset.filter(distance__lte=distance_object)

        return queryset


class ObservationFilter(FilterSet):
    counter = NumberInFilter(
        field_name="counter",
        lookup_expr="in",
        label="Counter id, the device(s) that produced the observations. \
            Separate values with commas if you intend to query with multiple counters.",
    )
    start_date = DateFilter(
        field_name="datetime",
        lookup_expr="gte",
        label="Start date of measurement period.",
    )
    end_date = DateFilter(
        field_name="datetime",
        method=filter_end_date,
        label="End date of measurement period.",
    )

    measurement_type = CharFilter(
        field_name="typeofmeasurement",
        lookup_expr="iexact",
        label="Type of measurement, often either `speed` or `count`.",
    )

    source = CharFilter(field_name="source", lookup_expr="iexact", label="Data source.")

    order = OrderingFilter(
        fields=(("datetime", "datetime"), ("counter_id", "counter")),
        field_labels={
            "datetime": "Datetime of observation to sort the results by.",
            "counter_id": "Counter",
        },
        label="Sort order for the results. \
            For example ascending = `datetime`, descending = `-datetime`.\
                Multiple filters can be combined by separating with comma.",
    )


class ObservationAggregateFilter(FilterSet):
    counter = NumberFilter(
        field_name="counter",
        required=True,
        lookup_expr="exact",
        label="Counter id, aggregates observations of selected counter.",
    )
    start_date = DateFilter(
        field_name="datetime",
        lookup_expr="gte",
        label="Start date of measurement period.",
    )
    end_date = DateFilter(
        field_name="datetime",
        method=filter_end_date,
        label="End date of measurement period.",
    )
    period = ChoiceFilter(
        field_name="period",
        required=True,
        lookup_expr="exact",
        label="Defines how long the aggregation period is.",
        choices=(
            ("hour", "hour"),
            ("day", "day"),
            ("month", "month"),
            ("year", "year"),
        ),
    )
    measurement_type = CharFilter(
        field_name="typeofmeasurement",
        required=True,
        lookup_expr="iexact",
        label="Type of measurement, often either `speed` or `count`. \
            Determines whether to use sum or average for aggregation.",
    )

    order = OrderingFilter(
        fields=(("start_time", "start_time"),),
        field_labels={
            "start_time": "Start time of observation to sort the results by.",
        },
        label="Sort order for the results. Ascending = `start_time`, descending = `-start_time`.",
    )


def filter_languages(queryset, name, value):
    queryset = queryset.annotate(description=F(f"description_{value}"))
    return queryset


class DatasourceFilter(FilterSet):
    language = ChoiceFilter(
        field_name="language",
        required=False,
        method=filter_languages,
        label="Determines the descriptions' language",
        choices=(("en", "English"), ("fi", "Finnish"), ("sv", "Swedish")),
    )
