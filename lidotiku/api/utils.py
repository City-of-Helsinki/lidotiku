sensorMeasurementTypes = {'count' : 'OHITUKSET', 'speed': 'KESKINOPEUS'}

def generateSensorName(type, duration, windowType='KIINTEA', direction='SUUNTA1'):
    sensorType = sensorMeasurementTypes[type]
    sensorDuration = duration // 60
    return f'{sensorType}_{sensorDuration}MIN_{windowType}_{direction}'


