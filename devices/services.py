import math
from django.db import transaction
from django.utils import timezone
from devices.models import DeviceLocation

def _haversine_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    import math as m
    phi1 = m.radians(float(lat1)); phi2 = m.radians(float(lat2))
    dphi = m.radians(float(lat2) - float(lat1))
    dlmb = m.radians(float(lon2) - float(lon1))
    a = m.sin(dphi/2)**2 + m.cos(phi1)*m.cos(phi2)*m.sin(dlmb/2)**2
    return 2 * R * m.asin(m.sqrt(a))

@transaction.atomic
def save_location_if_moved(device, latitude, longitude, min_distance_m=100):
    """
    - Se deslocou > min_distance_m: cria um NOVO registro com read_at=now.
    - Caso contrário: ATUALIZA o read_at do último registro para now.
    Retorna (created: bool, obj: DeviceLocation).
    """
    now = timezone.now()

    last = (DeviceLocation.objects
            .select_for_update()
            .filter(device=device)
            .only("id", "latitude", "longitude", "read_at")
            .order_by("-read_at")
            .first())

    if last:
        dist = _haversine_meters(last.latitude, last.longitude, latitude, longitude)
        if dist <= min_distance_m:
            # Não cria novo; apenas “refresca” a última leitura
            last.read_at = now
            last.save(update_fields=["read_at"])
            return False, last

    # Não tinha último ponto OU deslocou mais que o limiar → cria novo
    obj = DeviceLocation.objects.create(
        device=device,
        latitude=latitude,
        longitude=longitude,
        read_at=now,
    )
    return True, obj