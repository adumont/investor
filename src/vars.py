from pathlib import Path

CACHE_TTL = 6 * 60 * 60  # 6 horas

LOCAL_FILE = Path(__file__).parent.parent / "data" / "myinvestor.json"
LOCAL_FILE_TIMESTAMP = (
    "25/04/2026 11:24"  # Fecha y hora de la última actualización de los datos
)
