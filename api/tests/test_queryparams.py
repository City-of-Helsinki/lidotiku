import pytest
from django.urls import reverse
from api.models import Counter  # pylint: disable=import-error


@pytest.mark.django_db
def test_counter_params(api_client):
    url = reverse("counter-list")
    data = {"longitude": 60.234, "latitude": 10.123, "distance": 1.05}

    response = api_client.get(url, data=data)
    assert response.status_code == 200

    # All three query params are required
    del data["latitude"]
    response = api_client.get(url, data=data)
    assert response.status_code == 400

    data_required_all_missing = {}
    response = api_client.get(url, data=data_required_all_missing)
    assert response.status_code == 200


@pytest.mark.django_db
def test_counter_post_geojson(api_client):
    url = reverse("counter-list")
    valid_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [[24.5, 60.2], [24.5, 60.9], [24.8, 60.9], [24.8, 60.2], [24.5, 60.2]]
            ],
        },
    }
    response = api_client.post(url, data=valid_geojson, format="json")
    assert response.status_code == 200

    invalid_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[24.5, 60.2], [24.5, 60.9]]],
        },
    }

    response = api_client.post(url, data=invalid_geojson, format="json")
    assert response.status_code == 500

    invalid_random_json = {
        "type": "P",
        "geometry": {
            "type": "Poin",
            "coordina": [24.5, 60.2],
        },
    }

    response = api_client.post(url, data=invalid_random_json, format="json")
    assert response.status_code == 500


@pytest.mark.django_db
def test_observation_params_multiple_counters(api_client):
    url = reverse("observation-list")
    data = {"counter": ["1", "123", "543"]}
    counters_request = data["counter"]
    response = api_client.get(url, data=data)

    assert response.status_code == 200
    query_params = response.request.get("QUERY_STRING").split("&")
    counters_response = [x.split("=")[1] for x in query_params]
    assert all(counter in counters_request for counter in counters_response)
    assert len(counters_request) == len(counters_response)


@pytest.mark.django_db
def test_observation_aggregation_params(api_client):
    url = reverse("observation-aggregate-list")
    data = {"counter": "1", "period": "hour", "measurement_type": "count"}
    response = api_client.get(url, data=data)
    assert response.status_code == 200
    del data["period"]
    response = api_client.get(url, data)
    assert response.status_code == 400
    del data["measurement_type"]
    response = api_client.get(url, data)
    assert response.status_code == 400
    response = api_client.get(url, {})
    assert response.status_code == 400
    value_validation_data = {
        "counter": "1",
        "period": "second",
        "measurement_type": "count",
    }
    response = api_client.get(url, value_validation_data)
    assert response.status_code == 400
    value_validation_data = {
        "counter": "1",
        "period": "month",
        "measurement_type": "temperature",
    }
    response = api_client.get(url, value_validation_data)
    assert response.status_code == 400


@pytest.mark.django_db
def test_readonly_models():
    with pytest.raises(NotImplementedError):
        Counter.objects.create(id=1, name="Test")
    with pytest.raises(NotImplementedError):
        counter = Counter()
        counter.create(id=1, name="Test")
    counter = Counter(id=1, name="Test")
    with pytest.raises(NotImplementedError):
        counter.save()
    with pytest.raises(NotImplementedError):
        counter = Counter(id=1, name="Test")
        counter.update()
    with pytest.raises(NotImplementedError):
        counter.delete()
