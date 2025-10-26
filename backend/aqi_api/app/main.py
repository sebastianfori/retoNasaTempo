# backend/aqi_api/app/main.py

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from dotenv import load_dotenv

from app.core import (
    get_nearest_station,
    attach_latest_measurements,
    compute_aqi_summary,
    get_nearest_tempo_point,
    get_nearest_pixel,   # si no lo usás, podés quitarlo
    sanitize_json,
    combine_aqi_sources,
)
from app.tempo_cache import tempo_cache
from app.routers import auth
# from app.deps import require_auth   # si querés proteger /aqi

load_dotenv()

API_KEY = os.getenv("API_KEY")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
SESSION_SECRET  = os.getenv("SESSION_SECRET", "devsessionsecret")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chequeo temprano para evitar 500 confusos en /auth/google/login
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        raise RuntimeError(
            "GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET no configurados. "
            "Verifica backend/aqi_api/.env y que esté montado en docker-compose.yml (env_file)."
        )

    print("[STARTUP] Cargando cache inicial TEMPO...")
    try:
        tempo_cache.get_df()  # fuerza carga inicial
        print("[STARTUP] Cache inicial lista.")
    except Exception as e:
        print(f"[STARTUP][WARN] No se pudo cargar TEMPO al inicio: {e}")
    yield
    print("[SHUTDOWN] Cerrando API Air Quality...")


app = FastAPI(title="Air Quality API", version="1.1", lifespan=lifespan)

# 1) SessionMiddleware (Authlib necesita request.session)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,  # en prod con HTTPS: True
)

# 2) CORS (credenciales + origen explícito)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) Rutas de autenticación
app.include_router(auth.router)


@app.get("/aqi")  # , dependencies=[Depends(require_auth)]  # descomenta si querés protegerlo
def get_aqi(lat: float = Query(...), lon: float = Query(...)):
    """
    Devuelve la estación más cercana de OpenAQ y los datos de TEMPO más cercanos.
    """
    try:
        # --- 1. Buscar estación OpenAQ ---
        station = get_nearest_station(lat, lon, API_KEY)
        if not station:
            raise HTTPException(status_code=404, detail="No se encontraron estaciones cercanas")

        station = attach_latest_measurements(station, API_KEY)
        aqi_summary = compute_aqi_summary(station)  # si no usás la var, podés quitarla

        # --- 2. Cargar último archivo TEMPO (desde cache en memoria) ---
        df_tempo = tempo_cache.get_df()
        if df_tempo is None or len(df_tempo) == 0:
            raise HTTPException(status_code=503, detail="TEMPO no disponible (Azure/Blob)")

        tempo_row = get_nearest_tempo_point(df_tempo, lat, lon)

        tempo_data = {
            "nearest_lat": tempo_row["lat"],
            "nearest_lon": tempo_row["lon"],
            "distance_deg": tempo_row["dist"],
            "no2":   tempo_row.get("no2"),
            "o3tot": tempo_row.get("o3tot"),
            "o3prof":tempo_row.get("o3prof"),
            "hcho":  tempo_row.get("hcho"),
        }

        combined = combine_aqi_sources(station, tempo_data)

        # --- 3. Respuesta ---
        response = {
            "coordinates": {"lat": lat, "lon": lon},
            "station": {
                "id": station["id"],
                "name": station["name"],
                "distance_km": station["distance_km"],
            },
            "aqi": combined,
            "latest_measurements": station["latest_measurements"],
            "tempo_data": tempo_data,
        }
        return sanitize_json(response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# (opcional) Endpoint para verificar que el SessionMiddleware está activo
from fastapi import Request
@app.get("/debug/mw")
async def debug_mw(request: Request):
    return {"has_session": ("session" in request.scope)}
