from math import sin, cos, sqrt, atan2, radians

EARTH_RADIUS = 6373000.0


def coordinate_dis(coordinate1, coordinate2):
    """
    :param coordinate1: tuple(latitude1, longitude1)
    :param coordinate2: tuple(latitude2, longitude2)
    :return: distance between two coordinates in meters
    :functions from: www.kite.com/python/answers/how-to-find-the-distance-between-two-lat-long-coordinates-in-python
                     www.movable-type.co.uk/scripts/latlong.html
    """

    lat1, lon1 = radians(coordinate1[0]), radians(coordinate1[1])
    lat2, lon2 = radians(coordinate2[0]), radians(coordinate2[1])

    delta_lng = lon2 - lon1
    delta_lat = lat2 - lat1

    a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = EARTH_RADIUS * c
    return distance
