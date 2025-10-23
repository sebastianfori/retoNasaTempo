import os
import io
import pandas as pd
from azure.storage.blob import BlobServiceClient

def load_latest_parquet_from_blob(container_name: str = "tempo-data") -> pd.DataFrame:
    """
    Descarga el archivo Parquet más reciente desde un contenedor de Azure Blob Storage
    y lo carga en un DataFrame de pandas.
    """

    # Obtener cadena de conexión
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        raise EnvironmentError("Falta la variable AZURE_STORAGE_CONNECTION_STRING")

    # Crear cliente
    blob_service = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_service.get_container_client(container_name)

    # Listar blobs
    blobs = list(container_client.list_blobs())
    if not blobs:
        raise FileNotFoundError(f"No hay archivos en el contenedor '{container_name}'")

    # Ordenar por fecha de modificación
    latest_blob = max(blobs, key=lambda b: b.last_modified)
    print(f"Último archivo encontrado: {latest_blob.name} ({latest_blob.last_modified})")

    # Descargar el blob a memoria
    blob_data = container_client.download_blob(latest_blob.name).readall()

    # Cargar DataFrame desde bytes
    df = pd.read_parquet(io.BytesIO(blob_data))
    print(f"DataFrame cargado correctamente con {len(df):,} filas")

    return df
