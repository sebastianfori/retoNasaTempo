import os
from datetime import datetime
import logging
import sys
from azure.storage.blob import BlobServiceClient
import tempfile

# --- Configurar logger global con soporte UTF-8 ---
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def save_tempo_output(df, filename_prefix="tempo_full", filename=None):
    """
    Guarda el DataFrame localmente y, si USE_AZURE_BLOB=true,
    también lo sube a Azure Blob Storage con timestamp en el nombre.
    """
    try:
        use_blob = os.getenv("USE_AZURE_BLOB", "false").lower() == "true"

        tmp_dir = tempfile.gettempdir()
        output_dir = os.path.join(tmp_dir, os.getenv("OUTPUT_DIR", "tempo_cache"))
        os.makedirs(output_dir, exist_ok=True)

        # --- Determinar nombre base y timestamp ---
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        base_name = os.path.splitext(filename)[0] if filename else filename_prefix
        final_name = f"{base_name}_{timestamp}.parquet"
        local_path = os.path.join(output_dir, final_name)

        # --- Guardar localmente ---
        df.to_parquet(local_path)
        logger.info(f"✅ Archivo guardado localmente: {local_path}")

        # --- Subida opcional a Azure Blob Storage ---
        if use_blob:
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            container = os.getenv("BLOB_CONTAINER_NAME", "tempo-data")

            if not conn_str:
                logger.warning("⚠️ Falta AZURE_STORAGE_CONNECTION_STRING. Se mantiene archivo local.")
                return local_path

            try:
                blob_service = BlobServiceClient.from_connection_string(conn_str)
                container_client = blob_service.get_container_client(container)

                try:
                    container_client.create_container()
                except Exception:
                    # Ya existe
                    pass

                blob_name = os.path.basename(local_path)
                with open(local_path, "rb") as f:
                    container_client.upload_blob(blob_name, f, overwrite=True)

                logger.info(f"☁️ Archivo subido a Azure Blob Storage: {container}/{blob_name}")
                logger.info(f"🕒 Fecha y hora de subida (UTC): {timestamp}")

            except Exception as e:
                logger.error(f"💥 Error al subir a Azure Blob: {str(e)}", exc_info=True)

        return local_path

    except Exception as e:
        logger.error(f"💥 Error en save_tempo_output: {str(e)}", exc_info=True)
        raise
