import re

import pytest
from django.core.management import call_command
from django.test import Client


@pytest.mark.django_db
def test_browsable_api_static_files_in_production(settings, tmp_path):
    settings.DEBUG = False
    settings.STATIC_ROOT = tmp_path / "assets"
    settings.WHITENOISE_AUTOREFRESH = False
    settings.WHITENOISE_USE_FINDERS = False
    call_command("collectstatic", interactive=False, verbosity=0)

    client = Client()
    response = client.get("/api/", HTTP_ACCEPT="text/html")

    assert response.status_code == 200
    asset_urls = re.findall(
        rf'(?:href|src)="({re.escape(settings.STATIC_URL)}[^"]+)"',
        response.content.decode(),
    )
    assert any(url.endswith(".css") for url in asset_urls)
    assert any(url.endswith(".js") for url in asset_urls)

    for url in asset_urls:
        asset_response = client.get(url)
        assert asset_response.status_code == 200, url
        assert b"".join(asset_response.streaming_content), url
        if url.endswith(".css"):
            assert asset_response["Content-Type"].startswith("text/css"), url
        elif url.endswith(".js"):
            assert "javascript" in asset_response["Content-Type"], url
        asset_response.close()

    assert client.get(f"{settings.STATIC_URL}nonexistent.css").status_code == 404
