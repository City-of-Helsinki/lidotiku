from .sensors import data

sensorMeasurementTypes = {'count' : 'OHITUKSET', 'speed': 'KESKINOPEUS'}

def generateSensorName(type, duration, windowType='KIINTEA', direction='SUUNTA1'):
    sensorType = sensorMeasurementTypes[type]
    sensorDuration = duration // 60
    return f'{sensorType}_{sensorDuration}MIN_{windowType}_{direction}'

def getSensorInfo(sensorName):
    for sensor in data['sensors']:
        if sensor['name'] == sensorName:
            sensorId = int(sensor['id']) if sensor['id'] else None
            sensorShortName = sensor['shortName'] if sensor['shortName'] else None
            sensorUnit = sensor['unit'] if sensor['unit'] else None
            return {'id': sensorId, 'shortName': sensorShortName, 'unit' : sensorUnit}
    return {'id' : None, 'shortName': None, 'unit' : None}

