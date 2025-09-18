import os
from flask import current_app, send_from_directory, abort
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

def _azure_client():
    return BlobServiceClient.from_connection_string(
        current_app.config["AZURE_STORAGE_CONNECTION_STRING"]
    )

def save_media(file_storage) -> tuple[str, str]:
    """
    Returns (media_key, public_url_or_path).
    For local: media_key is filename; path is /media/<filename> route.
    For azure: media_key is blob name; url is https://.../container/blob
    """
    backend = current_app.config["STORAGE_BACKEND"]
    filename = file_storage.filename

    if backend == "local":
        os.makedirs(current_app.config["MEDIA_FOLDER"], exist_ok=True)
        dest = os.path.join(current_app.config["MEDIA_FOLDER"], filename)
        file_storage.save(dest)
        return filename, f"/media/{filename}"

    # azure
    container = current_app.config["AZURE_BLOB_CONTAINER"]
    client = _azure_client().get_blob_client(container=container, blob=filename)
    client.upload_blob(file_storage.stream, overwrite=True)
    return filename, client.url

def serve_local_media(filename: str):
    # Only for local backend
    folder = current_app.config["MEDIA_FOLDER"]
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(folder, filename, as_attachment=False)

def generate_download_url(media_key: str) -> str:
    """
    Returns a temporary, signed URL for client to download after payment.
    Local: signed /download?token=...
    Azure: SAS URL valid for 1 hour.
    """
    backend = current_app.config["STORAGE_BACKEND"]
    if backend == "local":
        # client will get /download?token=...
        return None  # handled at app layer via signed token
    # Azure SAS
    account_name = current_app.config["AZURE_STORAGE_ACCOUNT_NAME"]
    account_key = current_app.config["AZURE_STORAGE_ACCOUNT_KEY"]
    container = current_app.config["AZURE_BLOB_CONTAINER"]
    expiry = datetime.utcnow() + timedelta(hours=1)
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=media_key,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )
    return f"https://{account_name}.blob.core.windows.net/{container}/{media_key}?{sas}"
