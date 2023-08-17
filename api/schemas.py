from rest_framework.schemas.openapi import AutoSchema
from rest_framework.serializers import Serializer
from .views import CounterFilterValidationSerializer, ObservationFilterSerializer


class BaseSchema(AutoSchema):
    def _generate_query_parameters(
        self, serializer: Serializer, type_mappings: dict
    ) -> list[dict]:
        schema_parameters = []
        for field_name, field in serializer.get_fields().items():
            extra_parameter = {
                "name": f"{field_name}",
                "required": False,
                "in": "query",
                "description": field.label if field.label is not None else field_name,
                "schema": type_mappings.get(field_name, {"type": "string"}),
            }
            schema_parameters.append(extra_parameter)
        return schema_parameters


class CounterSchema(BaseSchema):
    def get_request_serializer(self, path, method):
        return CounterFilterValidationSerializer()

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        if operation.get("operationId", "").startswith("list"):
            serializer = self.get_request_serializer(path, method)
            type_mappings = {
                "latitude": {"type": "number", "format": "float"},
                "longitude": {"type": "number", "format": "float"},
                "distance": {"type": "number"},
            }
            parameters = self._generate_query_parameters(serializer, type_mappings)
            operation.get("parameters", [])[:0] = parameters
        return operation


class ObservationSchema(BaseSchema):
    def get_request_serializer(self, path, method):
        return ObservationFilterSerializer()

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
