import datetime
import logging
import azure.functions as func
import os
import time
import sys

# --- Forzar UTF-8 ---
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- Configurar logger unificado ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("tempo_function")

# --- Imports del paquete TEMPO ---
from tempo_core.credentials import get_tempo_credentials
from tempo_core.tempo_builder import build_full_tempo

# --- Inicializar Azure Function App ---
app = func.FunctionApp()

# --- Timer Trigger cada 2 horas ---
@app.schedule(
    schedule="0 0 */2 * * *",  # Cada 2 horas
    arg_name="timer",
    run_on_startup=True,
    use_monitor=True
)
def tempo_update(timer: func.TimerRequest):
    """
    Azure Function que actualiza datos TEMPO cada 2 horas.
    Se conecta al endpoint NASA EDL, obtiene credenciales temporales,
    descarga los últimos productos TEMPO y guarda el resultado en Azure Blob Storage.
    """

    start_time = datetime.datetime.utcnow()
    logger.info(f"TEMPO update triggered at {start_time.isoformat()} UTC")

    # --- Validar credenciales ---
    edl_user = os.getenv("EDL_USER")
    edl_pass = os.getenv("EDL_PASS")

    if not edl_user or not edl_pass:
        logger.error("Missing environment variables: EDL_USER or EDL_PASS")
        return

    # --- Reintentos automáticos ---
    MAX_RETRIES = 3
    RETRY_DELAY = 60  # segundos entre intentos

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} — starting TEMPO update pipeline")

            # 1️⃣ Obtener credenciales NASA temporales
            creds = get_tempo_credentials(edl_user, edl_pass)
            logger.info("NASA credentials obtained successfully")

            # 2️⃣ Construir y guardar el DataFrame TEMPO
            df_full = build_full_tempo(creds)
            logger.info(f"TEMPO updated successfully — {len(df_full):,} rows")

            duration = (datetime.datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Execution completed in {duration:.1f} seconds")
            return

        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {str(e)}", exc_info=True)
            if attempt < MAX_RETRIES:
                logger.warning(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("All attempts failed — aborting execution")

    logger.info("TEMPO update function finished (with errors).")
