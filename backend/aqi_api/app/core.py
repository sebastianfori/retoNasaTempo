import requests
from geopy.distance import geodesic
import pandas as pd
import numpy as np
import os
import io
from azure.storage.blob import BlobServiceClient
import math

# --- AQI breakpoints ---
AQI_BREAKPOINTS = {
    "pm25": [
        {"I_low": 0, "I_high": 50, "C_low": 0.0, "C_high": 12.0},
        {"I_low": 51, "I_high": 100, "C_low": 12.1, "C_high": 35.4},
        {"I_low": 101, "I_high": 150, "C_low": 35.5, "C_high": 55.4},
        {"I_low": 151, "I_high": 200, "C_low": 55.5, "C_high": 150.4},
        {"I_low": 201, "I_high": 300, "C_low": 150.5, "C_high": 250.4},
        {"I_low": 301, "I_high": 400, "C_low": 250.5, "C_high": 350.4},
        {"I_low": 401, "I_high": 500, "C_low": 350.5, "C_high": 500.4}
    ],
    "pm10": [
        {"I_low": 0, "I_high": 50, "C_low": 0, "C_high": 54},
        {"I_low": 51, "I_high": 100, "C_low": 55, "C_high": 154},
        {"I_low": 101, "I_high": 150, "C_low": 155, "C_high": 254},
        {"I_low": 151, "I_high": 200, "C_low": 255, "C_high": 354},
        {"I_low": 201, "I_high": 300, "C_low": 355, "C_high": 424},
        {"I_low": 301, "I_high": 400, "C_low": 425, "C_high": 504},
        {"I_low": 401, "I_high": 500, "C_low": 505, "C_high": 604}
    ],
    "o3": [
        {"I_low": 0, "I_high": 50, "C_low": 0.000, "C_high": 0.054},
        {"I_low": 51, "I_high": 100, "C_low": 0.055, "C_high": 0.070},
        {"I_low": 101, "I_high": 150, "C_low": 0.071, "C_high": 0.085},
        {"I_low": 151, "I_high": 200, "C_low": 0.086, "C_high": 0.105},
        {"I_low": 201, "I_high": 300, "C_low": 0.106, "C_high": 0.200}
    ],
    "co": [
        {"I_low": 0, "I_high": 50, "C_low": 0.0, "C_high": 4.4},
        {"I_low": 51, "I_high": 100, "C_low": 4.5, "C_high": 9.4},
        {"I_low": 101, "I_high": 150, "C_low": 9.5, "C_high": 12.4},
        {"I_low": 151, "I_high": 200, "C_low": 12.5, "C_high": 15.4},
        {"I_low": 201, "I_high": 300, "C_low": 15.5, "C_high": 30.4}
    ]
}


def calculate_aqi(concentration, breakpoints):
    for bp in breakpoints:
        if bp["C_low"] <= concentration <= bp["C_high"]:
            I_low, I_high = bp["I_low"], bp["I_high"]
            C_low, C_high = bp["C_low"], bp["C_high"]
            return round(((I_high - I_low) / (C_high - C_low)) * (concentration - C_low) + I_low, 1)
    return None


def get_nearest_station(lat, lon, api_key, radius_km=25):
    headers = {"X-API-Key": api_key}
    url = "https://api.openaq.org/v3/locations"
    params = {"coordinates": f"{lat},{lon}", "radius": radius_km * 1000, "limit": 100}

    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return None

    for s in results:
        s["distance_km"] = geodesic((lat, lon), (s["coordinates"]["latitude"], s["coordinates"]["longitude"])).km

    return min(results, key=lambda x: x["distance_km"])


def attach_latest_measurements(station, api_key):
    url = f"https://api.openaq.org/v3/locations/{station['id']}/latest"
    headers = {"X-API-Key": api_key}
    latest_data = requests.get(url, headers=headers).json()

    sensor_values = {
        item["sensorsId"]: {
            "value": item["value"],
            "datetime_utc": item["datetime"]["utc"],
            "datetime_local": item["datetime"]["local"]
        }
        for item in latest_data.get("results", [])
    }

    for sensor in station.get("sensors", []):
        sid = sensor["id"]
        sensor["latest"] = sensor_values.get(sid)

    station["latest_measurements"] = [
        {
            "parameter": s["parameter"]["displayName"],
            "value": s["latest"]["value"] if s["latest"] else None,
            "units": s["parameter"]["units"],
            "datetime": s["latest"]["datetime_local"] if s["latest"] else None
        }
        for s in station["sensors"] if s["latest"]
    ]
    return station

def compute_aqi_summary(station):
    """
    Calcula el AQI usando todos los contaminantes disponibles,
    manejando casos con pocas o nulas mediciones.
    """
    aqi_values = []

    for s in station.get("latest_measurements", []):
        param = s["parameter"].lower().replace("₂", "2").replace(".", "")
        value = s["value"]

        # solo si existe una tabla de AQI conocida
        if param in AQI_BREAKPOINTS and value is not None:
            aqi = calculate_aqi(value, AQI_BREAKPOINTS[param])
            if aqi is None:
                # si está por debajo del rango mínimo → AQI = 0 (aire excelente)
                if value < AQI_BREAKPOINTS[param][0]["C_low"]:
                    aqi = 0
            if aqi is not None:
                aqi_values.append({"parameter": param, "aqi": aqi, "value": value})

    # si no hay nada, intenta fallback
    if not aqi_values:
        # buscar parámetros secundarios
        secondaries = [s for s in station.get("latest_measurements", [])
                       if s["parameter"].lower().startswith(("no", "so2", "nh3"))]
        if secondaries:
            # fallback arbitrario, AQI leve si existen gases reactivos
            return {"aqi_value": 20, "category": "Buena", "dominant_pollutant": secondaries[0]["parameter"].upper()}
        else:
            return {"aqi_value": None, "category": "Sin datos", "dominant_pollutant": None}

    # calcular AQI dominante
    dominant = max(aqi_values, key=lambda x: x["aqi"])
    aqi_value = dominant["aqi"]

    if aqi_value <= 50:
        category = "Buena"
    elif aqi_value <= 100:
        category = "Moderada"
    elif aqi_value <= 150:
        category = "Dañina para grupos sensibles"
    elif aqi_value <= 200:
        category = "Dañina"
    elif aqi_value <= 300:
        category = "Muy dañina"
    else:
        category = "Peligrosa"

    return {
        "aqi_value": aqi_value,
        "category": category,
        "dominant_pollutant": dominant["parameter"].upper()
    }

def get_nearest_tempo_point(df: pd.DataFrame, lat: float, lon: float):
    """
    Dado un DataFrame de TEMPO (lat, lon, columnas de contaminantes)
    encuentra la fila más cercana al punto (lat, lon).
    """
    if df.empty:
        raise ValueError("El DataFrame TEMPO está vacío")

    # Calcular distancia euclidiana aproximada (en grados)
    df["dist"] = np.sqrt((df["lat"] - lat)**2 + (df["lon"] - lon)**2)
    nearest_row = df.loc[df["dist"].idxmin()].to_dict()
    return nearest_row

def get_nearest_pixel(df, lat, lon):
    lat_min, lat_max = lat - 0.1, lat + 0.1
    lon_min, lon_max = lon - 0.1, lon + 0.1
    subset = df.query("@lat_min < lat < @lat_max and @lon_min < lon < @lon_max")
    if subset.empty: return None
    return subset.iloc[((subset.lat - lat)**2 + (subset.lon - lon)**2).idxmin()]


def sanitize_json(obj):
    """Reemplaza NaN, +inf, -inf por None recursivamente."""
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    else:
        return obj

def compute_tempo_aqi(tempo_data):
    """
    Calcula un índice AQI extendido a partir de datos satelitales TEMPO (NO2, O3, HCHO).
    """
    SCALE_FACTORS = {
        "no2": 1e16,     # molec/cm²
        "o3tot": 300.0,  # DU
        "hcho": 2e16     # molec/cm²
    }

    WEIGHTS = {"no2": 0.5, "o3tot": 0.4, "hcho": 0.1}

    aqi_components = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for gas, factor in SCALE_FACTORS.items():
        val = tempo_data.get(gas)
        if val is None or (isinstance(val, float) and math.isnan(val)):
            aqi_components[gas.upper()] = None
            continue

        # Clamp y normalización
        rel = min(max(val / factor, 0.0), 2.0)
        sub_index = round(rel * 100, 1)
        aqi_components[gas.upper()] = sub_index

        weighted_sum += sub_index * WEIGHTS.get(gas, 1.0)
        total_weight += WEIGHTS.get(gas, 1.0)

    # Si no hay datos válidos
    if total_weight == 0:
        return {
            "tempo_aqi_value": None,
            "tempo_aqi_category": "Sin datos",
            "components": aqi_components
        }

    tempo_aqi_value = round(weighted_sum / total_weight, 1)

    # Categoría EPA-like
    if tempo_aqi_value <= 50:
        category = "Buena"
    elif tempo_aqi_value <= 100:
        category = "Moderada"
    elif tempo_aqi_value <= 150:
        category = "Dañina para grupos sensibles"
    elif tempo_aqi_value <= 200:
        category = "Dañina"
    elif tempo_aqi_value <= 300:
        category = "Muy dañina"
    else:
        category = "Peligrosa"

    return {
        "tempo_aqi_value": tempo_aqi_value,
        "tempo_aqi_category": category,
        "components": aqi_components
    }

def combine_aqi_sources(station, tempo_data=None):
    """
    Combina el AQI de superficie (OpenAQ) y el troposférico (TEMPO).
    """
    surface_aqi = compute_aqi_summary(station)

    if tempo_data:
        tempo_aqi = compute_tempo_aqi(tempo_data)
    else:
        tempo_aqi = {"tempo_aqi_value": None, "tempo_aqi_category": "Sin datos", "components": {}}

    combined = {
        "surface_aqi": surface_aqi,
        "tempo_aqi": tempo_aqi
    }

    # Si ambos existen, calcula una media ponderada simple
    if surface_aqi["aqi_value"] and tempo_aqi["tempo_aqi_value"]:
        combined["global_aqi"] = round(
            (surface_aqi["aqi_value"] * 0.7 + tempo_aqi["tempo_aqi_value"] * 0.3), 1
        )
    else:
        combined["global_aqi"] = surface_aqi["aqi_value"] or tempo_aqi["tempo_aqi_value"]

    return combined
