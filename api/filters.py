from django_filters import rest_framework as filters


class ObservationAggregateFilter(filters.FilterSet):
    counter = filters.NumberFilter(
        field_name="counter",
        required=True,
        lookup_expr="exact",
        label="Counter id, aggregates observations of selected counter.",
    )
    start_date = filters.DateFilter(
        field_name="start_time",
        lookup_expr="gte",
        label="Start date of measurement period.",
    )
    end_date = filters.DateFilter(
        field_name="start_time",
        lookup_expr="lte",
        label="End date of measurement period.",
    )
    period = filters.ChoiceFilter(
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
    measurement_type = filters.ChoiceFilter(
        field_name="typeofmeasurement",
        required=True,
        lookup_expr="exact",
        label="Type of measurement, often either `speed` or `count`. \
            Determines whether to use sum or average for aggregation.",
        choices=(("speed", "speed"), ("count", "count")),
    )

    order = filters.OrderingFilter(
        fields=(("start_time", "start_time"),),
        field_labels={
            "start_time": "Start time of observation to sort the results by.",
        },
        label="Sort order for the results. Ascending = `start_time`, descending = `-start_time`.",
    )
