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
        .filter(observation_count__gte=100)
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

    while response:
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)

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
    assert response.status_code == 200 and len(response.data["results"]) > 0

    while response:
        for observation in response.data["results"]:
            assert (observation["counter_id"]) in counter_ids
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)


@pytest.mark.django_db
def test_source_filter(api_client):
    url = reverse("observation-list")
    datasource_name = Datasource.objects.values_list("name", flat=True)[0]
    response = api_client.get(
        url, {"source": datasource_name, "page": 1, "page_size": 100}
    )
    assert response.status_code == 200 and len(response.data["results"]) > 0

    while response:
        response_observations = response.data["results"]
        for observation in response_observations:
            assert observation["source"] == datasource_name
        next_url = response.data["next"]
        if not next_url:
            break
        response = api_client.get(next_url)


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
    assert (
        valid_counters_response.status_code == 200
        and len(valid_counters_response.data["results"]) > 0
    )

    while valid_counters_response:
        for observation in valid_counters_response.data["results"]:
            assert observation["source"] == datasource_name
            assert observation["counter_id"] in valid_counter_ids
        next_url = valid_counters_response.data["next"]
        if not next_url:
            break
        valid_counters_response = api_client.get(next_url)

    invalid_counter_ids_response = api_client.get(
        url, {"source": datasource_name, "counter": invalid_counter_ids}
    )
    assert len(invalid_counter_ids_response.data["results"]) == 0
