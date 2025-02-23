from datetime import datetime, timedelta

import pytest
import pytz
from django.db.models import Count
from django.urls import reverse
from django.db.models.functions import TruncDate
from datetime import datetime

from api.models import Counter, Observation


@pytest.fixture()
def single_counter_parameters():
    counter = (
        Counter.objects.annotate(observation_count=Count("observation"))
        .filter(observation_count__gte=100)
        .first()
    )
    datetimes = list(
        Observation.objects.filter(counter_id=counter.id)
        .annotate(date=TruncDate("datetime"))
        .values_list("date", flat=True)
        .order_by("date")
        .distinct()[:10]
    )
    # Don't use the edge dates to ensure first and last hours of a given date both start/end date are included
    return {
        "start_date": str(datetimes[1]),
        "end_date": str(datetimes[-2]),
        "counter": counter.id,
        "measurement_type": "count",
    }


@pytest.fixture()
def min_date():
    return str(
        Observation.objects.annotate(date=TruncDate("datetime"))
        .values_list("date", flat=True)
        .order_by("date")
        .first()
    )


@pytest.fixture()
def max_date():
    return str(
        Observation.objects.annotate(date=TruncDate("datetime"))
        .values_list("date", flat=True)
        .order_by("-date")
        .first()
    )


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_observations_aggregate_date_filter(api_client, single_counter_parameters):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {**single_counter_parameters, "period": "hour", "order": "start_time"},
    )
    first_datetime = datetime.fromisoformat(response.data["results"][0]["start_time"])
    start_date = datetime.fromisoformat(single_counter_parameters["start_date"])
    start_datetime = pytz.timezone("Europe/Helsinki").localize(start_date)
    assert first_datetime == start_datetime

    while response:
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)
    last_datetime = datetime.fromisoformat(response.data["results"][-1]["start_time"])
    end_date = datetime.fromisoformat(single_counter_parameters["end_date"])
    # With the hour period aggregation we expect the last start_time to be 23:00 as it includes 23:00 to 23:59
    end_datetime = pytz.timezone("Europe/Helsinki").localize(end_date) + timedelta(
        hours=23
    )
    assert last_datetime == end_datetime


# Page contents do not overlap at datetime boundaries.
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_datetime_no_overlap(api_client, single_counter_parameters):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            **single_counter_parameters,
            "period": "hour",
            "order": "start_time",
            "page": 1,
        },
    )

    while response:
        for current_observation, next_observation in zip(
            response.data["results"], response.data["results"][1:]
        ):
            current_observation_datetime = datetime.fromisoformat(
                current_observation["start_time"]
            )
            next_observation_datetime = datetime.fromisoformat(
                next_observation["start_time"]
            )
            assert (
                next_observation_datetime
                == current_observation_datetime + timedelta(hours=1)
            )
        last_current_page_datetime = datetime.fromisoformat(
            response.data["results"][-1]["start_time"]
        )
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)
        first_next_page_datetime = datetime.fromisoformat(
            response.data["results"][0]["start_time"]
        )
        assert first_next_page_datetime == last_current_page_datetime + timedelta(
            hours=1
        )


# Ordering works and defaults to -datetime
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_default_ordering(api_client, single_counter_parameters):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            **single_counter_parameters,
            "period": "hour",
            "page": 1,
        },
    )

    while response:
        for current_observation, next_observation in zip(
            response.data["results"], response.data["results"][1:]
        ):
            assert current_observation["start_time"] > next_observation["start_time"]
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_reverse_ordering(api_client, single_counter_parameters):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            **single_counter_parameters,
            "period": "hour",
            "page": 1,
            "order": "start_time",
        },
    )

    while response:
        for current_observation, next_observation in zip(
            response.data["results"], response.data["results"][1:]
        ):
            assert current_observation["start_time"] < next_observation["start_time"]
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)


# Multiple counter id
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_multiple_counters(api_client, min_date, max_date):
    url = reverse("observation-aggregate-list")
    valid_counter_ids = (
        Counter.objects.filter(observation__isnull=False)
        .values_list("id", flat=True)
        .distinct()[:5]
    )
    response = api_client.get(
        url,
        {
            "start_date": min_date,
            "end_date": max_date,
            "measurement_type": "count",
            "period": "hour",
            "counter": valid_counter_ids,
            "page": 1,
            "order": "start_time",
        },
    )

    while response:
        for observation in response.data["results"]:
            assert observation["counter_id"] in valid_counter_ids
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)
