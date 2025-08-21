import pgeocode
import math
from functools import lru_cache

@lru_cache(maxsize=1)
def nomi():
    return pgeocode.Nominatim("us")

def zip_to_latlon(zip_code: str):
    z = str(zip_code).zfill(5)
    r = nomi().query_postal_code(z)
    if r is None or r.latitude is None or r.longitude is None:
        return None
    return float(r.latitude), float(r.longitude)

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c
