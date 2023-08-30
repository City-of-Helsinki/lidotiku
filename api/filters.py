from django_filters.rest_framework import (
    FilterSet,
    BaseInFilter,
    NumberFilter,
    ChoiceFilter,
    DateFilter,
    OrderingFilter,
)


class NumberInFilter(BaseInFilter, NumberFilter):
    pass


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
        lookup_expr="lte",
        label="End date of measurement period.",
    )

    measurement_type = ChoiceFilter(
        field_name="typeofmeasurement",
        lookup_expr="exact",
        label="Type of measurement, often either `speed` or `count`.",
        choices=(("speed", "speed"), ("count", "count")),
    )

    source = ChoiceFilter(
        field_name="source",
        lookup_expr="iexact",
        label="Data source. Please note taht choices might not be up to date.",
        choices=(
            ("EcoCounter", "EcoCounter"),
            ("FinTraffic", "FinTraffic"),
            ("HEL LAM", "HEL LAM"),
            ("InfoTripla", "InfoTripla"),
            ("Marksman", "Marksman"),
        ),
    )

    order = OrderingFilter(
        fields=(("datetime", "datetime"), ("counter", "counter")),
        field_labels={
            "datetime": "Datetime of observation to sort the results by.",
            "counter": "Counter",
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
        field_name="start_time",
        lookup_expr="gte",
        label="Start date of measurement period.",
    )
    end_date = DateFilter(
        field_name="start_time",
        lookup_expr="lte",
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
    measurement_type = ChoiceFilter(
        field_name="typeofmeasurement",
        required=True,
        lookup_expr="exact",
        label="Type of measurement, often either `speed` or `count`. \
            Determines whether to use sum or average for aggregation.",
        choices=(("speed", "speed"), ("count", "count")),
    )

    order = OrderingFilter(
        fields=(("start_time", "start_time"),),
        field_labels={
            "start_time": "Start time of observation to sort the results by.",
        },
        label="Sort order for the results. Ascending = `start_time`, descending = `-start_time`.",
    )
