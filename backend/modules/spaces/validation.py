from typing import Any
from backend.core.geo import validate_coordinates


ALLOWED_CATEGORIES = {
    "commercial",
    "coworking",
    "creative",
    "residential",
    "studio",
    "desk",
    "event",
}

ALLOWED_ACCESS_TYPES = {
    "smart_lock",
    "host_entry",
    "keycard",
    "security_guard",
    "lockbox",
}


def validate_space_payload(data: dict[str, Any], is_update: bool = False) -> tuple[bool, dict[str, Any], str | None]:
    """Validate and sanitize space listing payload.
    
    Returns:
        (is_valid, cleaned_data, error_message)
    """
    cleaned: dict[str, Any] = {}

    # Title
    if "title" in data or not is_update:
        title = str(data.get("title", "")).strip()
        if len(title) < 3 or len(title) > 200:
            return False, {}, "Title must be between 3 and 200 characters long."
        cleaned["title"] = title

    # Description
    if "description" in data:
        cleaned["description"] = str(data.get("description", "")).strip()

    # Category
    if "category" in data:
        cat = str(data.get("category", "commercial")).lower().strip()
        cleaned["category"] = cat if cat in ALLOWED_CATEGORIES else "commercial"
    elif not is_update:
        cleaned["category"] = "commercial"

    # Space Type
    if "space_type" in data or not is_update:
        st = str(data.get("space_type", "desk")).lower().strip()
        if not st:
            return False, {}, "space_type is required."
        cleaned["space_type"] = st

    # Price per hour / hourly_price
    price_val = data.get("hourly_price", data.get("price_per_hour"))
    if price_val is not None or not is_update:
        try:
            price = float(price_val)
            if price <= 0:
                return False, {}, "Hourly price must be greater than 0."
            cleaned["price_per_hour"] = price
            cleaned["price_per_day"] = float(data.get("price_per_day", price * 7.5))
        except (ValueError, TypeError):
            return False, {}, "Hourly price must be a valid positive number."

    # Minimum hours
    min_h_val = data.get("minimum_hours")
    if min_h_val is not None:
        try:
            min_h = int(min_h_val)
            if min_h < 1:
                return False, {}, "Minimum hours must be at least 1."
            cleaned["minimum_hours"] = min_h
        except (ValueError, TypeError):
            return False, {}, "Minimum hours must be an integer >= 1."
    elif not is_update:
        cleaned["minimum_hours"] = 1

    # Capacity / max_capacity
    cap_val = data.get("capacity") if "capacity" in data else data.get("max_capacity")
    if cap_val is not None:
        try:
            cap = int(cap_val)
            if cap < 1:
                return False, {}, "Capacity must be at least 1 person."
            cleaned["capacity"] = cap
        except (ValueError, TypeError):
            return False, {}, "Capacity must be a valid integer."
    elif not is_update:
        cleaned["capacity"] = 1

    # Coordinates
    lat_val = data.get("latitude")
    lon_val = data.get("longitude")
    if (lat_val is not None and lon_val is not None) or not is_update:
        try:
            lat = float(lat_val)
            lon = float(lon_val)
            if not validate_coordinates(lat, lon):
                return False, {}, "Invalid coordinates. Latitude must be in [-90, 90] and Longitude in [-180, 180]."
            cleaned["latitude"] = lat
            cleaned["longitude"] = lon
        except (ValueError, TypeError):
            return False, {}, "Latitude and Longitude must be valid numbers."

    # City & Location
    if "city" in data or not is_update:
        city = str(data.get("city", "")).strip()
        if not city:
            return False, {}, "City is required."
        cleaned["city"] = city

    if "address_line1" in data or "location" in data or not is_update:
        loc = str(data.get("address_line1", data.get("location", ""))).strip()
        if not loc:
            return False, {}, "Location address is required."
        cleaned["address_line1"] = loc
        cleaned["location"] = loc

    if "address_line2" in data:
        cleaned["address_line2"] = str(data.get("address_line2", "")).strip()
    if "neighborhood" in data:
        cleaned["neighborhood"] = str(data.get("neighborhood", "")).strip()
    if "state" in data:
        cleaned["state"] = str(data.get("state", "Karnataka")).strip()
    elif not is_update:
        cleaned["state"] = "Karnataka"
    if "pincode" in data:
        cleaned["pincode"] = str(data.get("pincode", "560001")).strip()
    elif not is_update:
        cleaned["pincode"] = "560001"

    # Sqft
    if "sqft" in data:
        try:
            sqft = float(data.get("sqft") or 0.0)
            if sqft < 0:
                return False, {}, "Square footage cannot be negative."
            cleaned["sqft"] = sqft
        except (ValueError, TypeError):
            return False, {}, "Square footage must be a valid number."

    # Geofence radius
    if "geofence_radius" in data:
        try:
            radius = float(data.get("geofence_radius", 50.0))
            if radius < 10.0 or radius > 1000.0:
                return False, {}, "Geofence radius must be between 10 and 1000 meters."
            cleaned["geofence_radius"] = radius
        except (ValueError, TypeError):
            return False, {}, "Geofence radius must be a number."
    elif not is_update:
        cleaned["geofence_radius"] = 50.0

    # Physical access type
    if "physical_access_type" in data:
        access = str(data.get("physical_access_type", "smart_lock")).lower().strip()
        cleaned["physical_access_type"] = access if access in ALLOWED_ACCESS_TYPES else "smart_lock"
    elif not is_update:
        cleaned["physical_access_type"] = "smart_lock"

    # Amenities, rules, images
    if "amenities" in data:
        am = data.get("amenities")
        cleaned["amenities"] = am if isinstance(am, list) else [str(am)]
    elif not is_update:
        cleaned["amenities"] = []

    if "rules" in data:
        cleaned["rules"] = str(data.get("rules", ""))

    if "images" in data:
        imgs = data.get("images")
        cleaned["images"] = imgs if isinstance(imgs, list) else [str(imgs)]
    elif not is_update:
        cleaned["images"] = []

    if "is_active" in data:
        cleaned["is_active"] = bool(data.get("is_active"))
    if "active_status" in data:
        cleaned["is_active"] = bool(data.get("active_status"))

    return True, cleaned, None
