import pytest
from django.urls import reverse

from api.models import Datasource


@pytest.mark.django_db
def test_default_ordering(api_client):
    url = reverse("sources-list")
    response = api_client.get(url)
    sources = response.data
    for current_source, next_source in zip(sources, sources[1:]):
        assert current_source["name"] < next_source["name"]


@pytest.mark.django_db
def test_default_english_description(api_client):
    url = reverse("sources-list")
    response = api_client.get(url)
    sources = response.data
    english_descriptions = Datasource.objects.values_list("description_en", flat=True)

    for source in sources:
        assert source["description"] in english_descriptions


@pytest.mark.django_db
def test_default_invalid_language_parameter(api_client):
    url = reverse("sources-list")
    response = api_client.get(url, {"language": "de"})

    assert response.status_code == 400
