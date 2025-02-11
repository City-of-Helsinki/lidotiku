import os

from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator
from .utils import sources_enum_parameter

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


class LidoSchemaGenerator(SchemaGenerator):
    def __init__(
        self,
        title=None,
        url=None,
        description=None,
        patterns=None,
        urlconf=None,
        version=None,
    ):
        title = title or "LIDO-TIKU API"
        url = url or "/"
        description = description or (
            "API for accessing traffic measurement data of the city of Helsinki. The measurement data is updated daily and hourly and consists of count and speed observations derived from sensor devices (counters) of different types (data sources), across different measurement intervals according the type of the sensor; typically 15 minutes. The sources include for example induction loops and pedestrian counters.\nThe city of Helsinki traffic open data made available from the LIDO-TIKU API is licensed under the Creative Commons 4.0 BY license according to the JHS-189 recommendation for public authorities in Finland. The license grants the right to use and distribute the data if the following attribution is included:\nSource: City of Helsinki, https://lidotiku.api.hel.fi/api/ , licence CC 4.0 BY: http://creativecommons.org/licenses/by/4.0/"
        )
        version = version or os.getenv("VERSION", "0.1")

        super().__init__(
            title=title,
            url=url,
            description=description,
            patterns=patterns,
            urlconf=urlconf,
            version=version,
        )
        self.license = {"name": "Creative Commons 4.0 BY", "identifier": "CC-BY-4.0"}
        self.summary = (
            "API for accessing traffic measurement data of the city of Helsinki."
        )

    def get_info(self):
        info = super().get_info()
        # Adds license and summary which are missing from SchemaGenerator
        if self.summary is not None:
            info["summary"] = self.summary
        if self.license is not None:
            info["license"] = self.license

        return info


class BaseSchema(AutoSchema):
    def __init__(self, request_serializer=None):
        if request_serializer is not None:
            self.request_serializer = request_serializer
        super().__init__()

    def get_request_serializer(self, path, method):
        if getattr(self, "request_serializer", None) is not None:
            return self.request_serializer()
        return super().get_serializer(path, method)

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET":
            parameters = operation.get("parameters", [])
            parameters.append(
                {
                    "name": "format",
                    "in": "query",
                    "description": "Output format",
                    "schema": {"type": "string", "enum": ["json", "api", "csv"]},
                }
            )
        return operation


class CounterSchema(BaseSchema):
    def get_filter_parameters(self, path: str, method: str):
        parameters = super().get_filter_parameters(path, method)
        return sources_enum_parameter(parameters, "source")

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        # This could be accomplished with drf-spectatular on the View with @extend_schema(parameters=[]) on the retrieve function
        if self.view.action == "retrieve":
            operation["parameters"] = [
                param for param in operation["parameters"] if param.get("name") == "id"
            ]
        if method == "GET" and operation.get("operationId", "").startswith("list"):
            result_schema = operation["responses"]["200"]["content"][
                "application/json"
            ]["schema"]["properties"]["results"]
            feature_collection = {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "example": "FeatureCollection"},
                    "features": {"type": "array", "items": result_schema["items"]},
                },
            }
            operation["responses"]["200"]["content"]["application/json"]["schema"][
                "properties"
            ]["results"] = feature_collection
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
    def get_filter_parameters(self, path: str, method: str):
        parameters = super().get_filter_parameters(path, method)
        return sources_enum_parameter(parameters, "source")

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if method == "GET" and operation.get("operationId", "").startswith("list"):
            # Fixes OpenAPI types (defaults to string)
            type_mappings = {
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
                "counter": {"type": "array", "format": "int64"},
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


class DatasourceSchema(BaseSchema):
    def get_path_parameters(self, path: str, method: str):
        parameters = super().get_path_parameters(path, method)
        return sources_enum_parameter(parameters, "name")

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        return operation
