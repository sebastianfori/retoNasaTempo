import boto3
import json
import re
import logging
import sys
from datetime import datetime, timedelta, timezone

# --- Configurar logger global con soporte UTF-8 ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_latest_tempo_file_for_region(
    s3,
    bucket,
    target_dt,
    region,
    prefix,
    hours_step=3,
    max_days=5
):
    """
    Busca el archivo TEMPO más reciente dentro de intervalos de `hours_step` horas hacia atrás,
    con un límite total de `max_days` días (por defecto, 5 días = 40 iteraciones).

    - Recorre cada bloque de 3 horas hacia atrás (por defecto).
    - Dentro de cada bloque, busca archivos NetCDF (.nc / .nc4) correspondientes a la región (G01–G09).
    - Devuelve el más reciente que exista dentro de cualquier bloque del rango de 5 días.

    Si no se encuentra nada, devuelve {"Key": None, "LastModified": None}.
    """

    max_iter = int((24 / hours_step) * max_days)
    search_dt = target_dt

    for i in range(max_iter):
        date_prefix = search_dt.strftime("%Y.%m.%d")
        prefix_full = f"{prefix}/{date_prefix}/"

        logger.info(
            f"🔎 [{i+1:02d}/{max_iter}] Buscando archivos en: {prefix_full} "
            f"para región {region} ({search_dt:%Y-%m-%d %H:%M UTC})"
        )

        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix_full)
        except Exception as e:
            logger.warning(f"⚠️ Error al acceder al bucket: {e}")
            return {"Key": None, "LastModified": None}

        if "Contents" in resp:
            # Filtrar archivos válidos
            def is_valid_nc(key: str, region: str) -> bool:
                pattern = re.compile(rf"_S\d{{3}}{region.upper()}\.(?:NC|NC4)$", re.IGNORECASE)
                return bool(pattern.search(key))

            files = [obj for obj in resp["Contents"] if is_valid_nc(obj["Key"], region)]

            if files:
                latest = max(files, key=lambda x: x["LastModified"])
                key = latest["Key"]
                mod_time = latest["LastModified"]
                logger.info(f"✅ Archivo encontrado ({mod_time}): {key}")
                return {
                    "Key": key,
                    "LastModified": mod_time.isoformat() if hasattr(mod_time, "isoformat") else mod_time
                }

        # Si no hay archivos, retrocede
        search_dt -= timedelta(hours=hours_step)

    logger.error(
        f"❌ No se encontraron archivos válidos en las últimas {max_days} días "
        f"(pasos de {hours_step} h) para región {region}."
    )
    return {"Key": None, "LastModified": None}


def get_latest_tempo_key_products(creds, target_dt=None):
    """
    Devuelve los archivos más recientes por producto y región
    utilizando credenciales temporales de NASA S3.
    """
    if target_dt is None:
        target_dt = datetime.now(timezone.utc)

    s3 = boto3.client(
        "s3",
        aws_access_key_id=creds["accessKeyId"],
        aws_secret_access_key=creds["secretAccessKey"],
        aws_session_token=creds["sessionToken"]
    )

    bucket = "asdc-prod-protected"
    regions = [f"G0{i}" for i in range(1, 10)]
    products = {
        "NO2_L2_V04": "TEMPO/TEMPO_NO2_L2_V04",
        "O3TOT_L2_V04": "TEMPO/TEMPO_O3TOT_L2_V04",
        "O3PROF_L2_V04": "TEMPO/TEMPO_O3PROF_L2_V04",
        "HCHO_L2_V04": "TEMPO/TEMPO_HCHO_L2_V04"
    }

    logger.info("🚀 Iniciando búsqueda de productos TEMPO más recientes en S3...")
    results = []

    for prod_name, prefix in products.items():
        logger.info(f"📂 Producto: {prod_name}")
        for region in regions:
            res = get_latest_tempo_file_for_region(s3, bucket, target_dt, region, prefix)
            results.append({
                "product": prod_name,
                "region": region,
                "Key": res["Key"],
                "LastModified": res["LastModified"]
            })

    logger.info(f"✅ Búsqueda completada. Total de registros: {len(results)}")
    return results
