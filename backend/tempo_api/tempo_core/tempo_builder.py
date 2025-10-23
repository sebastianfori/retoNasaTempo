import os
import pandas as pd
from datetime import datetime, timezone
import logging
import sys

from tempo_core.tempo_fetch import get_latest_tempo_key_products
from tempo_core.tempo_merge import merge_tempo_tiles
from tempo_core.tempo_storage import save_tempo_output


# --- Configurar logger global con soporte UTF-8 ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def build_full_tempo(creds):
    """
    Descarga, combina y guarda los productos TEMPO más recientes
    usando las credenciales temporales de NASA.
    """
    try:
        logger.info("🚀 Iniciando actualización de TEMPO...")
        target_dt = datetime.now(timezone.utc)

        # 🔹 Paso 1: Buscar archivos más recientes
        logger.info("🔎 Buscando claves más recientes en S3...")
        archivos = get_latest_tempo_key_products(creds, target_dt)
        logger.info(f"📦 {len(archivos)} resultados obtenidos. Iniciando descarga...")

        # 🔹 Paso 2: Descargar y procesar archivos
        logger.info("⬇️ Ejecutando merge_tempo_tiles() — iniciando descarga y parsing...")
        df_no2, df_o3tot, df_o3prof, df_hcho = merge_tempo_tiles(archivos, creds)

        # 🔹 Paso 3: Unir resultados
        logger.info("🧩 Uniendo productos en un único DataFrame...")
        df_final = (
            df_no2[["lat", "lon", "no2_l2_v04"]]
            .merge(df_o3tot[["lat", "lon", "o3tot_l2_v04"]], on=["lat", "lon"], how="outer")
            .merge(df_o3prof[["lat", "lon", "o3prof_l2_v04"]], on=["lat", "lon"], how="outer")
            .merge(df_hcho[["lat", "lon", "hcho_l2_v04"]], on=["lat", "lon"], how="outer")
        ).rename(
            columns={
                "no2_l2_v04": "no2",
                "o3tot_l2_v04": "o3tot",
                "o3prof_l2_v04": "o3prof",
                "hcho_l2_v04": "hcho",
            }
        )

        # 🔹 Paso 4: Guardar resultado final
        logger.info("💾 Guardando resultado final...")
        path = save_tempo_output(df_final, filename="tempo_full.parquet")
        logger.info(f"✅ Archivo final guardado en {path}")

        return df_final

    except Exception as e:
        logger.error(f"💥 Error en build_full_tempo: {str(e)}", exc_info=True)
        raise
