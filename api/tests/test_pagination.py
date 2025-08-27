import math
import secrets

import pytest
from django.db.models import Count
from django.urls import reverse

from api.models import Counter, Observation
from api.views import CounterViewSet


@pytest.fixture()
def observation_parameters():
    counter = (
        Counter.objects.annotate(observation_count=Count("observation"))
        .filter(observation_count__gte=100)
        .first()
    )
    datetimes = list(
        Observation.objects.order_by("-datetime")
        .filter(counter_id=counter.id)
        .values_list("datetime", flat=True)[:10000]
    )
    return {
        "start_date": datetimes[-1].date(),
        "end_date": datetimes[0].date(),
        "counter": counter.id,
        "page_size": 1000,
    }


# Observations should default to cursor pagination
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_cursor_default(api_client, observation_parameters):
    url = reverse("observation-list")
    response = api_client.get(url)
    assert "cursor" in response.data["next"]

    response = api_client.get(url, {**observation_parameters})
    assert "cursor" in response.data["next"]


# Observations when provided a page should use page number pagination
@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_page_number_parameter(api_client, observation_parameters):
    url = reverse("observation-list")
    response = api_client.get(url, {"page": 1})
    assert "cursor" not in response.data["next"]

    response = api_client.get(
        url,
        {
            **observation_parameters,
            "page": 2,
        },
    )
    assert "cursor" not in response.data["next"] and "page=3" in response.data["next"]


# Default observations ordering is -datetime for both cursor and page number pagination
@pytest.mark.django_db
def test_observations_default_ordering(api_client):
    url = reverse("observation-list")
    page_num_response = api_client.get(url)
    assert (
        page_num_response.status_code == 200
        and len(page_num_response.data["results"]) > 0
    )

    observations = page_num_response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] >= next_observation["datetime"]

    response = api_client.get(url, {"page": "1"})
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] >= next_observation["datetime"]


# Reverse observations ordering works for both cursor & page number pagination
@pytest.mark.django_db
def test_observations_reverse_ordering(api_client):
    url = reverse("observation-list")
    response = api_client.get(url, {"order": "datetime"})
    assert response.status_code == 200 and len(response.data["results"]) > 0

    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] <= next_observation["datetime"]

    response = api_client.get(url, {"order": "datetime", "page": "1"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] <= next_observation["datetime"]


# If only counter order parameter provided, counter criteria takes precedence
@pytest.mark.django_db
def test_observations_counter_ordering(api_client):
    url = reverse("observation-list")
    response = api_client.get(url, {"order": "counter"})
    assert response.status_code == 200 and len(response.data["results"]) > 0

    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] <= next_observation["counter_id"]

    response = api_client.get(url, {"order": "counter", "page": "1"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] <= next_observation["counter_id"]


# Counter reverse ordering
@pytest.mark.django_db
def test_observations_counter_reverse_ordering(api_client):
    url = reverse("observation-list")
    response = api_client.get(url, {"order": "-counter"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] >= next_observation["counter_id"]

    response = api_client.get(url, {"order": "-counter", "page": "1"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] >= next_observation["counter_id"]


# Cursor pagination: if datetime and counter both provided, first takes precedence
@pytest.mark.django_db
def test_observations_cursor_both_order_parameters(api_client):
    # Cursor pagination
    url = reverse("observation-list")
    response = api_client.get(url, {"order": "datetime,-counter"})
    assert response.status_code == 200 and len(response.data["results"]) > 0

    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] <= next_observation["datetime"]

    response = api_client.get(url, {"order": "counter,-datetime"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] >= next_observation["counter_id"]


# PageNumber pagination: response includes an accurate total count
@pytest.mark.django_db
def test_page_number_pagination_observation_total_count(api_client):
    url = reverse("observation-list")
    response = api_client.get(url, {"page": 1, "page_size": 1000})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    total_count = response.data["count"]
    final_page_response = api_client.get(url, {"page": math.ceil(total_count / 1000)})
    assert (final_page_response.data["next"]) is None


# PageNumber pagination: For datetime and counter both provided, first takes precedence
@pytest.mark.django_db
def test_observations_both_order_parameters(api_client):
    # Cursor pagination
    url = reverse("observation-list")
    response = api_client.get(url, {"order": "datetime,-counter", "page": "3"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["datetime"] <= next_observation["datetime"]

    response = api_client.get(url, {"order": "counter,-datetime", "page": "3"})
    assert response.status_code == 200 and len(response.data["results"]) > 0
    observations = response.data["results"]
    for current_observation, next_observation in zip(observations, observations[1:]):
        assert current_observation["counter_id"] >= next_observation["counter_id"]


@pytest.mark.django_db
def test_cursor_validity(api_client):
    url = reverse("observation-list")
    response = api_client.get(url)

    second_page_url = response.data["next"]
    second_page_response = api_client.get(second_page_url)
    assert (
        second_page_response.status_code == 200
        and len(second_page_response.data["results"]) > 0
    )
    assert (
        response.data["results"][-1]["datetime"]
        >= second_page_response.data["results"][0]["datetime"]
    )

    third_page_url = second_page_response.data["next"]
    third_page_response = api_client.get(third_page_url)
    assert (
        third_page_response.status_code == 200
        and len(third_page_response.data["results"]) > 0
    )
    assert (
        second_page_response.data["results"][-1]["datetime"]
        >= third_page_response.data["results"][0]["datetime"]
    )

    previous_page_url = third_page_response.data["previous"]
    previous_page_response = api_client.get(previous_page_url)
    assert previous_page_response.data == second_page_response.data


@pytest.mark.filterwarnings(
    "ignore:DateTimeField Observation.datetime received a naive datetime"
)
@pytest.mark.django_db
def test_cursor_validity_end(api_client, observation_parameters):
    url = reverse("observation-list")
    response = api_client.get(url, {**observation_parameters})
    assert response.status_code == 200 and len(response.data["results"]) > 0

    while response.data["next"]:
        next_response = api_client.get(response.data["next"])
        assert (
            response.data["results"][-1]["datetime"]
            >= next_response.data["results"][0]["datetime"]
        )
        response = next_response

    assert response.data["next"] is None and response.data["previous"]


# PageNumber pagination: response includes an accurate total count
@pytest.mark.django_db
def test_page_number_pagination_total_count(api_client):
    url = reverse("counter-list")
    response = api_client.get(url, {"page": 1})
    total_count = response.data["count"]
    page_size = len(response.data["results"]["features"])
    num_pages = math.ceil(total_count / page_size)
    final_page_response = api_client.get(url, {"page": num_pages})
    assert (final_page_response.data["next"]) is None


# Query paramater page_size=0 will use the default page size
@pytest.mark.django_db
def test_page_size_zero(api_client):
    url = reverse("counter-list")
    response = api_client.get(url, {"page_number": 0})
    default_page_size = CounterViewSet.pagination_class().page_size
    assert len(response.data["results"]["features"]) == default_page_size


# Page size less than max can be set and returns a valid next link
@pytest.mark.django_db
def test_provided_page_size(api_client):
    url = reverse("counter-list")
    max_page_size = CounterViewSet.pagination_class().max_page_size
    # Secrets randbelow returns an int in the range [0, exclusive_upper_bound]
    random_page_size = secrets.randbelow(max_page_size) + 1
    response = api_client.get(url, {"page_size": random_page_size})
    assert len(response.data["results"]["features"]) == random_page_size
    second_page_url = response.data["next"]
    second_page_response = api_client.get(second_page_url)
    previous_page_response = api_client.get(second_page_response.data["previous"])
    assert previous_page_response.data == response.data


# Last page has no next link
@pytest.mark.django_db
def test_last_page_no_next_link(api_client):
    url = reverse("counter-list")
    first_page_response = api_client.get(url, {"page": 1})
    total_count = first_page_response.data["count"]
    page_size = len(first_page_response.data["results"]["features"])
    num_pages = math.ceil(total_count / page_size)
    final_page_response = api_client.get(url, {"page": num_pages})
    assert (final_page_response.data["next"]) is None
