import base64
import json
import requests
import os
import sys
import logging

# --- Configuración de entorno y codificación ---
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_ALL"] = "C.UTF-8"

# En algunos entornos, sys.stdout no tiene método reconfigure (Python <3.7)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- Configurar logger global ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_tempo_credentials(
    username,
    password,
    endpoint="https://data.asdc.earthdata.nasa.gov/s3credentials"
):
    """
    Returns temporary (~1h) NASA credentials for accessing TEMPO data from AWS S3.
    """

    try:
        logger.info("🔐 Iniciando obtención de credenciales NASA...")

        # Primera solicitud para iniciar el flujo de login
        login_resp = requests.get(endpoint, allow_redirects=False, timeout=30)
        login_resp.raise_for_status()

        auth = f"{username}:{password}"
        encoded_auth = base64.b64encode(auth.encode("utf-8")).decode("utf-8")

        # Enviar credenciales al redirect
        redirect_url = login_resp.headers.get("location")
        logger.debug(f"Redirigiendo autenticación a: {redirect_url}")

        auth_redirect = requests.post(
            redirect_url,
            data={"credentials": encoded_auth},
            headers={"Origin": endpoint},
            allow_redirects=False,
            timeout=30
        )
        auth_redirect.raise_for_status()

        # Seguir la cadena de redirecciones hasta obtener token
        final_redirect = auth_redirect.headers.get("location")
        final = requests.get(final_redirect, allow_redirects=False, timeout=30)
        results = requests.get(
            endpoint,
            cookies={"accessToken": final.cookies.get("accessToken")},
            timeout=30
        )
        results.raise_for_status()

        # Decodificar JSON con seguridad UTF-8
        credentials = json.loads(results.content.decode("utf-8", errors="replace"))
        logger.info("✅ Credenciales NASA obtenidas correctamente.")

        return credentials

    except Exception as e:
        # Siempre registrar errores en UTF-8
        logger.error(f"💥 Error al obtener credenciales NASA: {str(e)}", exc_info=True)
        raise
