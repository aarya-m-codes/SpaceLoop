import math

# WGS-84 Mean Earth Radius in meters
EARTH_RADIUS_METERS = 6371000.0
EARTH_RADIUS_KM = 6371.0


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """Validate latitude (-90 to 90) and longitude (-180 to 180) WGS-84 ranges."""
    try:
        lat = float(latitude)
        lon = float(longitude)
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except (TypeError, ValueError):
        return False


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in meters using the Haversine formula."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_METERS * c


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    return haversine_distance_meters(lat1, lon1, lat2, lon2) / 1000.0


def is_within_geofence(
    user_lat: float,
    user_lon: float,
    target_lat: float,
    target_lon: float,
    radius_meters: float = 50.0,
) -> tuple[bool, float]:
    """Determine if a user's coordinate is within a given radius of a target location.
    
    Returns:
        (is_inside, distance_in_meters)
    """
    if not (validate_coordinates(user_lat, user_lon) and validate_coordinates(target_lat, target_lon)):
        raise ValueError("Invalid coordinates supplied for geofence calculation.")

    distance = haversine_distance_meters(user_lat, user_lon, target_lat, target_lon)
    return distance <= radius_meters, distance


def get_bounding_box(lat: float, lon: float, radius_km: float) -> dict[str, float]:
    """Calculate the min/max latitude and longitude bounding box for indexing and spatial queries."""
    if not validate_coordinates(lat, lon):
        raise ValueError("Invalid coordinates supplied for bounding box calculation.")

    lat_delta = radius_km / 111.0  # ~111 km per degree latitude
    lon_delta = radius_km / (111.0 * math.cos(math.radians(lat)))

    return {
        "min_lat": max(-90.0, lat - lat_delta),
        "max_lat": min(90.0, lat + lat_delta),
        "min_lon": max(-180.0, lon - lon_delta),
        "max_lon": min(180.0, lon + lon_delta),
    }
