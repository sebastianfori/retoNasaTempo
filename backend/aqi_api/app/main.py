from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from app.core import get_nearest_station, attach_latest_measurements, compute_aqi_summary, get_nearest_tempo_point, get_nearest_pixel
from app.azure_blob_reader import load_latest_parquet_from_blob
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from app.core import sanitize_json
from app.tempo_cache import tempo_cache
from app.core import combine_aqi_sources
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

API_KEY = os.getenv("API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[STARTUP] Cargando cache inicial TEMPO...")
    tempo_cache.get_df()  # fuerza la carga inicial al arrancar
    print("[STARTUP] Cache inicial lista.")
    yield
    print("[SHUTDOWN] Cerrando API Air Quality...")
app = FastAPI(title="Air Quality API", version="1.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ajustá a tus hosts en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/aqi")
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
        # --- 2. Cargar último archivo TEMPO desde Azure ---

        aqi_summary = compute_aqi_summary(station)

        df_tempo = tempo_cache.get_df()

        tempo_row = get_nearest_tempo_point(df_tempo, lat, lon)

        tempo_data = {
                "nearest_lat": tempo_row["lat"],
                "nearest_lon": tempo_row["lon"],
                "distance_deg": tempo_row["dist"],
                "no2": tempo_row.get("no2"),
                "o3tot": tempo_row.get("o3tot"),
                "o3prof": tempo_row.get("o3prof"),
                "hcho": tempo_row.get("hcho")
            }

        combined = combine_aqi_sources(station, tempo_data)

        # --- 3. Combinar resultados ---
        response = {
            "coordinates": {"lat": lat, "lon": lon},
            "station": {
                "id": station["id"],
                "name": station["name"],
                "distance_km": station["distance_km"]
            },
            "aqi": combined,
            "latest_measurements": station["latest_measurements"],
            "tempo_data": tempo_data
        }
        return sanitize_json(response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

