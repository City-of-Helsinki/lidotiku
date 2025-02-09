from datetime import datetime, timedelta

import pytest
import pytz
from django.db.models import Count
from django.urls import reverse
from django.utils.timezone import make_aware

from api.models import Counter, Observation


@pytest.fixture()
def aggregate_observation_parameters():
    counter = (
        Counter.objects.annotate(observation_count=Count("observation"))
        .filter(observation_count__gte=10000)
        .first()
    )
    datetimes = list(
        Observation.objects.order_by("datetime")
        .filter(counter_id=counter.id)
        .values_list("datetime", flat=True)[:10000]
    )
    return {
        "start_date": datetimes[0].date(),
        "end_date": datetimes[-1].date(),
        "counter": counter.id,
        "measurement_type": "count",
    }


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_observations_aggregate_date_filter(
    api_client, aggregate_observation_parameters
):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            **aggregate_observation_parameters,
            "period": "hour",
        },
    )
    first_datetime = datetime.fromisoformat(response.data["results"][0]["start_time"])
    start_datetime = make_aware(
        datetime.combine(
            aggregate_observation_parameters["start_date"], datetime.min.time()
        ),
        timezone=pytz.timezone("Europe/Helsinki"),
    )
    assert first_datetime >= start_datetime

    while response.data["next"]:
        next_response = api_client.get(response.data["next"])
        response = next_response
    last_datetime = datetime.fromisoformat(response.data["results"][-1]["start_time"])
    end_datetime = make_aware(
        datetime.combine(
            aggregate_observation_parameters["end_date"], datetime.max.time()
        ),
        timezone=pytz.timezone("Europe/Helsinki"),
    )
    assert last_datetime <= end_datetime


# Page contents do not overlap at datetime boundaries.
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_datetime_no_overlap(api_client, aggregate_observation_parameters):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            **aggregate_observation_parameters,
            "period": "hour",
            "order": "start_time",
            "page": 1,
            "page_size": 3,
        },
    )

    while response.data["next"]:
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
        response = api_client.get(response.data["next"])
        first_next_page_datetime = datetime.fromisoformat(
            response.data["results"][0]["start_time"]
        )
        assert first_next_page_datetime == last_current_page_datetime + timedelta(
            hours=1
        )


# Ordering works and defaults to -datetime,(counter_id,direction)
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_default_ordering(api_client):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            "start_date": "2023-02-01",
            "end_date": "2023-02-04",
            "period": "hour",
            "measurement_type": "count",
            "counter": 1,
            "page": 1,
            "page_size": 3,
        },
    )

    while response.data["next"]:
        for current_observation, next_observation in zip(
            response.data["results"], response.data["results"][1:]
        ):
            assert current_observation["start_time"] > next_observation["start_time"]
        response = api_client.get(response.data["next"])


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_reverse_ordering(api_client):
    url = reverse("observation-aggregate-list")
    response = api_client.get(
        url,
        {
            "start_date": "2023-02-01",
            "end_date": "2023-02-04",
            "period": "hour",
            "measurement_type": "count",
            "counter": 1,
            "page": 1,
            "page_size": 3,
            "order": "start_time",
        },
    )

    while response.data["next"]:
        for current_observation, next_observation in zip(
            response.data["results"], response.data["results"][1:]
        ):
            assert current_observation["start_time"] < next_observation["start_time"]
        response = api_client.get(response.data["next"])


# Multiple counter id


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_multiple_counters(api_client):
    url = reverse("observation-aggregate-list")
    valid_counter_ids = (
        Counter.objects.filter(observation__isnull=False)
        .values_list("id", flat=True)
        .distinct()[:5]
    )
    response = api_client.get(
        url,
        {
            "start_date": "2023-02-01",
            "end_date": "2023-02-04",
            "period": "hour",
            "measurement_type": "count",
            "counter": valid_counter_ids,
            "page": 1,
            "page_size": 3,
            "order": "start_time",
        },
    )

    while response.data["next"]:
        for observation in response.data["results"]:
            assert observation["counter_id"] in valid_counter_ids
        response = api_client.get(response.data["next"])
