import pytest
from django.urls import reverse
from django.contrib.gis.geos import GEOSGeometry, Point
from django.contrib.gis.db.models.functions import Distance
from geopy.distance import geodesic
from api.models import Datasource, Counter
from api.views import CounterViewSet


@pytest.fixture
def middle_counter():
    counters = Counter.objects.all().order_by("longitude")
    return counters[len(counters) // 2]


@pytest.fixture
def geojson_area():
    return {
        "type": "Polygon",
        "coordinates": [
            [[24.5, 60.2], [24.5, 60.9], [24.8, 60.9], [24.98, 59.9], [24.5, 60.2]]
        ],
    }


# Distance filter returns valid counters within the given distance
@pytest.mark.django_db
def test_coordinates_distance(api_client, middle_counter):
    url = reverse("counter-list")
    query_point_params = {
        "latitude": middle_counter.latitude,
        "longitude": middle_counter.longitude,
        "distance": 2,
        "page_size": CounterViewSet.pagination_class().max_page_size,
    }
    response = api_client.get(url, query_point_params)

    while response:
        counters = response.data["results"]["features"]
        for counter in counters:
            counter_point = Point(
                x=counter["geometry"]["coordinates"][0],
                y=counter["geometry"]["coordinates"][1],
                srid=4326,
            )
            assert (
                geodesic(
                    (middle_counter.latitude, middle_counter.longitude),
                    (counter_point.y, counter_point.x),
                )
                <= 2.0
            )
        if response.data["next"]:
            response = api_client.get(response.data["next"])
        else:
            break


# Zero distance should only return the exact counter whose coordinates given as parameters
@pytest.mark.django_db
def test_coordinates_zero_distance(api_client):
    url = reverse("counter-list")
    response = api_client.get(url)
    counter = response.data["results"]["features"]
    counter_coordinates = counter[0]["geometry"]["coordinates"]
    query_point_params = {
        "latitude": counter_coordinates[1],
        "longitude": counter_coordinates[0],
        "distance": 0,
    }
    counter_response = api_client.get(url, query_point_params)
    assert len(counter_response.data["results"]["features"]) == 1

    response_point = response.data["results"]["features"][0]
    assert counter_coordinates[0] == response_point["geometry"]["coordinates"][0]
    assert counter_coordinates[1] == response_point["geometry"]["coordinates"][1]


@pytest.mark.django_db
def test_single_source_filter(api_client):
    url = reverse("counter-list")
    datasource_name = Datasource.objects.values_list("name", flat=True)[0]
    response = api_client.get(
        url,
        {
            "source": datasource_name,
            "page_size": CounterViewSet.pagination_class().max_page_size,
        },
    )
    while response:
        counters = response.data["results"]["features"]
        for counter in counters:
            assert counter["properties"]["source"] == datasource_name

        if response.data["next"]:
            response = api_client.get(response.data["next"])
        else:
            break


@pytest.mark.django_db
def test_multiple_source_filter(api_client):
    url = reverse("counter-list")
    datasource_names = Datasource.objects.values_list("name", flat=True)
    datasource_names_subset = datasource_names[: (len(datasource_names) // 2)]
    response = api_client.get(
        url,
        {
            "source": ",".join(datasource_names_subset),
            "page_size": CounterViewSet.pagination_class().max_page_size,
        },
    )
    while response:
        counters = response.data["results"]["features"]
        for counter in counters:
            assert counter["properties"]["source"] in datasource_names_subset

        if response.data["next"]:
            response = api_client.get(response.data["next"])
        else:
            break


@pytest.mark.django_db
def test_single_source_multiple_counters_distance_filter(api_client, middle_counter):
    url = reverse("counter-list")
    response = api_client.get(
        url,
        {
            "source": middle_counter.source,
            "latitude": middle_counter.latitude,
            "longitude": middle_counter.longitude,
            "distance": 2,
            "page_size": CounterViewSet.pagination_class().max_page_size,
        },
    )
    while response:
        counters = response.data["results"]["features"]
        for counter in counters:
            counter_point = Point(
                x=counter["geometry"]["coordinates"][0],
                y=counter["geometry"]["coordinates"][1],
                srid=4326,
            )
            assert (
                geodesic(
                    (middle_counter.latitude, middle_counter.longitude),
                    (counter_point.y, counter_point.x),
                )
                <= 2.0
            )
            assert counter["properties"]["source"] == middle_counter.source

        if response.data["next"]:
            response = api_client.get(response.data["next"])
        else:
            break


@pytest.mark.django_db
def test_multple_source_multiple_counters_distance_filter(api_client, middle_counter):
    url = reverse("counter-list")
    datasource_names = Datasource.objects.values_list("name", flat=True)
    datasource_names_subset = datasource_names[: (len(datasource_names) // 2)]
    response = api_client.get(
        url,
        {
            "source": ",".join(datasource_names_subset),
            "latitude": middle_counter.latitude,
            "longitude": middle_counter.longitude,
            "distance": 2,
            "page_size": CounterViewSet.pagination_class().max_page_size,
        },
    )
    while response:
        response_counters = response.data["results"]["features"]
        for counter in response_counters:
            counter_point = Point(
                x=counter["geometry"]["coordinates"][0],
                y=counter["geometry"]["coordinates"][1],
                srid=4326,
            )
            assert (
                geodesic(
                    (middle_counter.latitude, middle_counter.longitude),
                    (counter_point.y, counter_point.x),
                )
                <= 2.0
            )
            assert counter["properties"]["source"] in datasource_names_subset

        if response.data["next"]:
            response = api_client.get(response.data["next"])
        else:
            break


# Returned counters should be within the provided GeoJSON area
@pytest.mark.django_db
def test_geojson_area_filter(api_client, geojson_area):
    url = reverse("counter-list")
    response = api_client.post(url, data=geojson_area, format="json")
    geometry = GEOSGeometry(str(geojson_area), srid=4326)
    response_counters = response.data["features"]
    for counter in response_counters:
        counter_point = Point(
            x=counter["geometry"]["coordinates"][0],
            y=counter["geometry"]["coordinates"][1],
            srid=4326,
        )
        assert geometry.contains(counter_point)

    outside_counters = Counter.objects.exclude(geom__within=geometry)
    for counter in outside_counters:
        counter_point = Point(
            y=counter.latitude,
            x=counter.longitude,
            srid=4326,
        )
        assert not geometry.contains(counter_point)
