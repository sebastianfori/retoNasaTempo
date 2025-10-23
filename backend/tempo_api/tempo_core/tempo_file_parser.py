from netCDF4 import Dataset
import numpy as np
import pandas as pd
import os
import logging
import sys

# --- Configurar logger global con soporte UTF-8 ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def tempo_file_to_df(local_path, product_name=None):
    """
    Abre un archivo TEMPO .nc y devuelve un DataFrame con lat/lon/valor principal.
    Incluye control de calidad por flags y reemplazo de valores inválidos.
    """
    try:
        logger.info(f"📂 Procesando archivo: {local_path}")
        nc = Dataset(local_path, "r")

        if product_name is None:
            product_name = os.path.basename(local_path).split("_")[1]
        product_name = product_name.upper()

        # --- Geolocalización ---
        lat = nc.groups["geolocation"].variables["latitude"][:]
        lon = nc.groups["geolocation"].variables["longitude"][:]

        # --- Productos individuales ---
        if "NO2" in product_name:
            main = nc.groups["product"].variables["vertical_column_troposphere"][:]
            flag = nc.groups["product"].variables["main_data_quality_flag"][:]

        elif "O3TOT" in product_name:
            main = nc.groups["product"].variables["column_amount_o3"][:]
            flag = nc.groups["support_data"].variables["ground_pixel_quality_flag"][:]

        elif "O3PROF" in product_name:
            o3_prof = nc.groups["product"].variables["ozone_profile"][:]
            flag = nc.groups["qa_statistics"].variables["exit_status"][:]

            # Promediamos solo los primeros 10 niveles (troposfera)
            main = np.nanmean(o3_prof[:, :, :10], axis=2)
            main = np.where(flag > 1, np.nan, main)
            main = np.where(main < 0, np.nan, main)

        elif "HCHO" in product_name:
            main = nc.groups["product"].variables["vertical_column"][:]
            flag = nc.groups["product"].variables["main_data_quality_flag"][:]

        else:
            raise ValueError(f"Producto no reconocido: {product_name}")

        # --- Limpieza de datos inválidos ---
        main = np.where(flag > 1, np.nan, main)
        main = np.where(main < 0, np.nan, main)

        # --- Construcción del DataFrame ---
        df = pd.DataFrame({
            "lon": lon.flatten(),
            "lat": lat.flatten(),
            product_name.lower(): main.flatten(),
            "q": flag.flatten()
        }).dropna(subset=[product_name.lower()])

        df["source"] = os.path.basename(local_path)
        df["product"] = product_name

        nc.close()
        logger.info(f"✅ Archivo procesado correctamente: {os.path.basename(local_path)} ({len(df):,} filas)")
        return df

    except Exception as e:
        logger.error(f"⚠️ Error procesando {local_path}: {str(e)}", exc_info=True)
        return pd.DataFrame()
