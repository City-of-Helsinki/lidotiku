from rest_framework.schemas.openapi import AutoSchema

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


def get_date_format_example(field_name):
    return {
        f"{field_name}": {
            "summary": "Date format",
            "value": "2023-01-31",
        }
    }


class BaseSchema(AutoSchema):
    def __init__(self, request_serializer=None):
        if request_serializer is not None:
            self.request_serializer = request_serializer
        super().__init__()

    def get_request_serializer(self, path, method):
        if getattr(self, "request_serializer", None) is not None:
            return self.request_serializer()
        return super().get_serializer(path, method)


class CounterSchema(BaseSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET" and operation.get("operationId", "").startswith("list"):
            # Fixes OpenAPI types (defaults to string)
            type_mappings = {
                "latitude": {"type": "number", "format": "float"},
                "longitude": {"type": "number", "format": "float"},
                "distance": {"type": "number"},
            }
            parameters = operation.get("parameters", [])
            for parameter in parameters:
                if parameter["name"] in type_mappings:
                    parameter["schema"] = type_mappings.get(parameter["name"])
        # Attempts to generate OpenAPI schema for GeoJSON query in body
        if method == "POST":
            request_body_content_json = (
                operation.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
            )
            request_body_content_json["schema"] = GEOJSON_POLYGON_JSONSCHEMA
            request_body_content_json["examples"] = {
                "polygon": {
                    "summary": "Query with GeoJSON Polygon",
                    "value": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [24.5, 60.2],
                                [24.5, 60.9],
                                [24.8, 60.9],
                                [24.8, 60.2],
                                [24.5, 60.2],
                            ]
                        ],
                    },
                }
            }
            # Automatically generated for HTTP201, but this is not creating anything.
            del operation["responses"]["201"]
            operation["responses"]["200"] = {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Counter"},
                        }
                    }
                },
            }
        return operation

    def map_field(self, field):
        if field.field_name == "geometry":
            return {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["Point"]},
                    "coordinates": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 2,
                        "items": {"type": "number", "format": "float"},
                    },
                },
            }

        return super().map_field(field)


class ObservationSchema(BaseSchema):
    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET" and operation.get("operationId", "").startswith("list"):
            # Fixes OpenAPI types (defaults to string)
            type_mappings = {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "counter": {"type": "integer", "format": "int64"},
            }

            parameters = operation.get("parameters", [])
            for parameter in parameters:
                name = parameter["name"]
                if name in type_mappings:
                    parameter["schema"] = type_mappings.get(name)
                if name in ["start_date", "end_date"]:
                    parameter["examples"] = get_date_format_example(name)
                if name == "counter":
                    parameter["examples"] = {
                        "counter_multiple": {
                            "summary": "Multiple counters",
                            "value": "1,23,79",
                        },
                        "single": {
                            "summary": "Single counter",
                            "value": "83",
                        },
                    }

        return operation


class ObservationAggregateSchema(ObservationSchema):
    def get_operation_id(self, path, method):
        # The operation id (or name) is generated from the model,
        # thus this needs to be done manually to avoid conflict
        operation_id = super().get_operation_id(path, method)
        operation_id = f"{operation_id}Aggregate"
        return operation_id
