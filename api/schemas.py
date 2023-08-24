from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import Serializer

GEOJSON_POLYGON_JSONSCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://geojson.org/schema/Polygon.json",
    "title": "GeoJSON Polygon",
    "type": "object",
    "required": ["type", "coordinates"],
    "properties": {
        "type": {"type": "string", "enum": ["Polygon"]},
        "coordinates": {
            "type": "array",
            "items": {
                "type": "array",
                "minItems": 4,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "items": {"type": "number"},
                },
            },
        },
        "bbox": {
            "type": "array",
            "minItems": 4,
            "items": {"type": "number"},
        },
    },
}


class BaseSchema(AutoSchema):
    def __init__(self, request_serializer=None):
        if request_serializer is not None:
            self.request_serializer = request_serializer
        super().__init__()

    def get_request_serializer(self, path, method):
        if self.request_serializer is not None:
            return self.request_serializer()
        return super().get_serializer(path, method)

    def _generate_query_parameters(
        self, serializer: Serializer, type_mappings: dict
    ) -> list[dict]:
        schema_parameters = []
        for field_name, field in serializer.get_fields().items():
            extra_parameter = {
                "name": f"{field_name}",
                "required": getattr(field, "required", False),
                "in": "query",
                "description": field.label if field.label is not None else field_name,
                "schema": type_mappings.get(field_name, {"type": "string"}),
            }
            schema_parameters.append(extra_parameter)
        return schema_parameters


class CounterSchema(BaseSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET" and operation.get("operationId", "").startswith("list"):
            serializer = self.get_request_serializer(path, method)
            type_mappings = {
                "latitude": {"type": "number", "format": "float"},
                "longitude": {"type": "number", "format": "float"},
                "distance": {"type": "number"},
            }
            parameters = self._generate_query_parameters(serializer, type_mappings)
            operation.get("parameters", [])[:0] = parameters
        # Attempts to generate OpenAPI schema for GeoJSON query in body
        if method == "POST":
            operation.get("requestBody", {}).get("content", {}).get(
                "application/json", {}
            )["schema"] = GEOJSON_POLYGON_JSONSCHEMA
        return operation


class ObservationSchema(BaseSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if operation.get("operationId", "").startswith("list"):
            serializer = self.get_request_serializer(path, method)
            type_mappings = {
                "counter": {"type": "integer"},
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "measurement_type": {"type": "string"},
                "order": {"type": "string", "enum": ["asc", "desc"]},
            }
            parameters = self._generate_query_parameters(serializer, type_mappings)
            operation.get("parameters", [])[:0] = parameters
        return operation


class ObservationAggregationSchema(BaseSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if operation.get("operationId", "").startswith("list"):
            serializer = self.get_request_serializer(path, method)
            type_mappings = {
                "counter": {"type": "integer"},
                "start_time": {"type": "string", "format": "date-time"},
                "end_time": {"type": "string", "format": "date-time"},
                "measurement_type": {"type": "string"},
                "order": {"type": "string", "enum": ["asc", "desc"]},
            }
            parameters = self._generate_query_parameters(serializer, type_mappings)
            operation.get("parameters", [])[:0] = parameters
        return operation
