from typing import Tuple
from django.http import JsonResponse, HttpRequest
from django.db import connection, DatabaseError, Error
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured, AppRegistryNotReady


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


def health_check(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "OK"}, status=200)


def readiness(_request: HttpRequest) -> JsonResponse:
    readiness_status = {
        "database": _database_is_ready(),
        "application": _app_is_ready(),
    }
    if all(readiness_status.values()):
        return JsonResponse({"status": "ready"}, status=200)

    return JsonResponse({"status": "not ready"}, status=503)