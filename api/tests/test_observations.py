import math
from datetime import datetime

import pytest
import pytz
from django.db.models import Count
from django.urls import reverse
from django.utils.timezone import make_aware

from api.models import Counter, Datasource, Observation


@pytest.fixture()
def observation_parameters():
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
        "page_size": 1000,
    }


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_date_range_filter(api_client, observation_parameters):
    url = reverse("observation-list")
    response = api_client.get(
        url,
        {**observation_parameters},
    )
    first_datetime = datetime.fromisoformat(response.data["results"][0]["datetime"])
    start_datetime = make_aware(
        datetime.combine(observation_parameters["start_date"], datetime.min.time()),
        pytz.timezone("Europe/Helsinki"),
    )
    assert first_datetime >= start_datetime

    while response.data["next"]:
        next_response = api_client.get(response.data["next"])
        response = next_response
    last_datetime = datetime.fromisoformat(response.data["results"][-1]["datetime"])
    end_datetime = make_aware(
        datetime.combine(observation_parameters["end_date"], datetime.max.time())
    )
    assert last_datetime <= end_datetime


@pytest.mark.django_db
def test_multiple_counter_filter(api_client):
    url = reverse("observation-list")
    counter_ids = (
        Counter.objects.filter(observation__isnull=False)
        .distinct()
        .values_list("id", flat=True)[:5]
    )
    response = api_client.get(url, {"counter": counter_ids})

    for observation in response.data["results"]:
        assert (observation["counter_id"]) in counter_ids


@pytest.mark.django_db
def test_source_filter(api_client):
    url = reverse("observation-list")
    datasource_name = Datasource.objects.values_list("name", flat=True)[0]
    response = api_client.get(
        url, {"source": datasource_name, "page": 1, "page_size": 1000}
    )
    total_count = response.data["count"]
    total_pages = math.ceil(total_count / 1000)

    # Only check 10 pages for speed, there may be a large count of pages
    page_interval = total_pages // (10)
    i = 1
    while i <= total_pages:
        response = api_client.get(
            url,
            {"source": datasource_name, "page": i, "page_size": 1000},
        )
        response_observations = response.data["results"]
        for observation in response_observations:
            assert observation["source"] == datasource_name
        i += page_interval


@pytest.mark.django_db
def test_source_and_counter_filter(api_client):
    url = reverse("observation-list")
    datasource_names = Datasource.objects.values_list("name", flat=True)
    datasource_name = datasource_names[0]
    valid_counter_ids = (
        Counter.objects.filter(source=datasource_name, observation__isnull=False)
        .values_list("id", flat=True)
        .distinct()[:5]
    )
    invalid_counter_ids = (
        Counter.objects.exclude(source=datasource_name)
        .distinct()
        .values_list("id", flat=True)[:5]
    )

    valid_counters_response = api_client.get(
        url, {"source": datasource_name, "counter": valid_counter_ids, "page": 1}
    )
    total_count = valid_counters_response.data["count"]
    total_pages = math.ceil(total_count / 1000)
    page_interval = total_pages // (10)

    i = page_interval
    while i <= total_pages:
        for observation in valid_counters_response.data["results"]:
            assert observation["source"] == datasource_name
            assert observation["counter_id"] in valid_counter_ids
        valid_counters_response = api_client.get(
            url, {"source": datasource_name, "counter": valid_counter_ids, "page": i}
        )
        i += page_interval

    invalid_counter_ids_response = api_client.get(
        url, {"source": datasource_name, "counter": invalid_counter_ids}
    )
    assert len(invalid_counter_ids_response.data["results"]) == 0
