from api.models import Datasource


# Converts a paramater from string literal to enum with source names
def sources_enum_parameter(parameters, parameter_name):
    datasource_names = Datasource.objects.values_list("name", flat=True)
    return [
        (
            {**parameter, "schema": {"type": "string", "enum": datasource_names}}
            if parameter["name"] == parameter_name
            else parameter
        )
        for parameter in parameters
    ]
