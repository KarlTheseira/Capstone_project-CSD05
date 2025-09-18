from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def signer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="download-link")

def create_signed_token(media_key: str) -> str:
    return signer().dumps({"media_key": media_key})

def verify_signed_token(token: str, max_age_seconds: int = 3600) -> str | None:
    try:
        data = signer().loads(token, max_age=max_age_seconds)
        return data.get("media_key")
    except Exception:
        return None
