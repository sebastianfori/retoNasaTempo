import os
import boto3
import pandas as pd
import logging
import sys
from tempo_core.tempo_file_parser import tempo_file_to_df

# --- Configurar logger global con soporte UTF-8 ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def merge_tempo_tiles(results, creds, download_dir=None):
    import tempfile, os, boto3, pandas as pd
    from tempo_core.tempo_file_parser import tempo_file_to_df

    # Si no se especifica, usar carpeta temporal segura
    if download_dir is None:
        download_dir = os.path.join(tempfile.gettempdir(), "tempo_tiles")

    os.makedirs(download_dir, exist_ok=True)

    """
    Descarga archivos TEMPO desde S3, los procesa con `tempo_file_to_df`
    y devuelve los DataFrames combinados para cada producto (NO2, O3TOT, O3PROF, HCHO).
    """

    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=creds["accessKeyId"],
            aws_secret_access_key=creds["secretAccessKey"],
            aws_session_token=creds["sessionToken"]
        )

        bucket = "asdc-prod-protected"
        os.makedirs(download_dir, exist_ok=True)
        dfs = {"NO2": [], "O3TOT": [], "O3PROF": [], "HCHO": []}

        logger.info("⬇️ Iniciando descarga y procesamiento de archivos TEMPO...")

        for entry in results:
            key = entry.get("Key")
            product = entry.get("product", "UNKNOWN").upper()
            region = entry.get("region", "G??")

            if not key:
                logger.warning(f"⚠️ {product}-{region}: sin archivo válido, se omite.")
                continue

            filename = os.path.join(download_dir, os.path.basename(key))

            # --- Descargar archivo ---
            if not os.path.exists(filename):
                logger.info(f"📥 Descargando {product}-{region} desde S3...")
                try:
                    s3.download_file(bucket, key, filename)
                    logger.info(f"✅ Descarga completa: {filename}")
                except Exception as e:
                    logger.error(f"💥 Error descargando {key}: {str(e)}", exc_info=True)
                    continue
            else:
                logger.info(f"📦 {filename} ya existe, se omite descarga.")

            # --- Convertir a DataFrame ---
            df = tempo_file_to_df(filename, product_name=product)
            if df.empty:
                logger.warning(f"⚠️ {product}-{region}: sin datos válidos tras procesar.")
                continue

            # Clasificar por tipo de producto
            for k in dfs.keys():
                if k in product:
                    dfs[k].append(df)
                    logger.info(f"🧩 {product}-{region}: {len(df):,} filas añadidas.")
                    break

        logger.info("✅ Descarga y procesamiento completados. Uniendo DataFrames...")

        return (
            pd.concat(dfs["NO2"], ignore_index=True) if dfs["NO2"] else pd.DataFrame(),
            pd.concat(dfs["O3TOT"], ignore_index=True) if dfs["O3TOT"] else pd.DataFrame(),
            pd.concat(dfs["O3PROF"], ignore_index=True) if dfs["O3PROF"] else pd.DataFrame(),
            pd.concat(dfs["HCHO"], ignore_index=True) if dfs["HCHO"] else pd.DataFrame(),
        )

    except Exception as e:
        logger.error(f"💥 Error en merge_tempo_tiles: {str(e)}", exc_info=True)
        raise
