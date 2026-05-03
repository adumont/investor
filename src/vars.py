from pathlib import Path

CACHE_TTL = 6 * 60 * 60  # 6 horas

LOCAL_FILE = Path(__file__).parent.parent / "data" / "myinvestor.json"
LOCAL_FILE_TIMESTAMP = (
    "25/04/2026 11:24"  # Fecha y hora de la última actualización de los datos
)

MYINVESTOR_API_URL = (
    "https://api.myinvestor.es/myinvestor-server/rest/public/fondos/find-fondos"
    "?tipo=TODOS&token=a2e8e18ad26a079c576038f0ad4fa18ce0d9e415f5bf6f43f89cf3831a0e4685__"
)
