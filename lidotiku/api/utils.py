from .sensors import SENSOR_DETAILS

sensor_measurement_types = {"count": "OHITUKSET", "speed": "KESKINOPEUS"}


def generate_sensor_name(
    measurement_type, duration, window_type="KIINTEA", direction="SUUNTA1"
):
    sensor_type = sensor_measurement_types[measurement_type]
    sensor_duration = duration // 60
    return f"{sensor_type}_{sensor_duration}MIN_{window_type}_{direction}"


def get_sensor_info(sensor_name):
    for sensor in SENSOR_DETAILS["sensors"]:
        if sensor["name"] == sensor_name:
            sensor_id = int(sensor.get("id"))
            sensor_short_name = sensor.get("shortName")
            sensor_unit = sensor.get("unit")
            return {
                "id": sensor_id,
                "short_name": sensor_short_name,
                "unit": sensor_unit,
            }
    return {"id": None, "short_name": None, "unit": None}
