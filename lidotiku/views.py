import os
from typing import Tuple
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.db import connection, DatabaseError, Error
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


def _app_is_ready() -> bool:
    try:
        apps.check_apps_ready()
        apps.check_models_ready()
        return True
    except (AppRegistryNotReady, ImproperlyConfigured, ImportError):
        return False


def _database_is_ready() -> Tuple[bool, None] | Tuple[bool, Exception]:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            if row is None:
                raise DatabaseError("Unable to fetch from database")
            return True, None
    except (ImproperlyConfigured, DatabaseError, Error, ImportError) as error:
        return False, error


@require_GET
@csrf_exempt
def health_check(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "OK"}, status=200)


@require_GET
@csrf_exempt
def readiness(_request: HttpRequest) -> JsonResponse:
    readiness_status = {
        "database": _database_is_ready(),
        "application": _app_is_ready(),
    }
    if all(readiness_status.values()):
        return JsonResponse({"status": "ready"}, status=200)

    return JsonResponse({"status": "not ready"}, status=503)


@require_GET
@csrf_exempt
def swagger_ui(_request: HttpRequest):
    url = os.getenv("HOST", "localhost:8000")
    # pylint: disable=line-too-long
    html = (
        """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta
          name="description"
          content="SwaggerUI"
        />
        <title>SwaggerUI</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css" />
      </head>
      <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js" crossorigin></script>
      <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-standalone-preset.js" crossorigin></script>
      <script>
        window.onload = () => {
          window.ui = SwaggerUIBundle({"""
        + f"url: '{'http' if 'localhost' in url else 'https'}://{url}/openapi-schema.json',"
        + """
            dom_id: '#swagger-ui',
            presets: [
              SwaggerUIBundle.presets.apis,
              SwaggerUIStandalonePreset
            ],
            layout: "StandaloneLayout",
          });
        };
      </script>
      </body>
    </html>"""
    )
    return HttpResponse(html)
