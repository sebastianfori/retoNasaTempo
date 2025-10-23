# app/tempo_cache.py
import time
import threading
from datetime import datetime, timedelta
import pandas as pd
from app.azure_blob_reader import load_latest_parquet_from_blob

CACHE_TTL = timedelta(hours=2)

class TempoCache:
    def __init__(self):
        self.df = None
        self.last_update = None
        self.lock = threading.Lock()
        self._start_background_refresh()

    def _start_background_refresh(self):
        t = threading.Thread(target=self._auto_refresh, daemon=True)
        t.start()

    def _auto_refresh(self):
        while True:
            try:
                if self.needs_refresh():
                    print("[TEMPO CACHE] Refreshing cache from Azure Blob...")
                    df = load_latest_parquet_from_blob()
                    with self.lock:
                        self.df = df
                        self.last_update = datetime.utcnow()
                    print(f"[TEMPO CACHE] Updated successfully with {len(df):,} rows.")
                else:
                    print("[TEMPO CACHE] Still valid; skipping refresh.")
            except Exception as e:
                print(f"[TEMPO CACHE] Error refreshing cache: {e}")
            time.sleep(CACHE_TTL.total_seconds())

    def needs_refresh(self):
        if self.df is None or self.last_update is None:
            return True
        return datetime.utcnow() - self.last_update > CACHE_TTL

    def get_df(self):
        with self.lock:
            if self.df is not None:
                return self.df

        print("[TEMPO CACHE] Cache empty, loading for first time...")
        df = load_latest_parquet_from_blob()
        with self.lock:
            self.df = df
            self.last_update = datetime.utcnow()
        return df


# instancia global
tempo_cache = TempoCache()

