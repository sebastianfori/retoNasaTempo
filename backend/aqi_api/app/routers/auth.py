# backend/aqi_api/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/auth", tags=["auth"])

config = Config(environ=os.environ)
oauth = OAuth(config)

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "1440"))
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

SESSION_COOKIE = "app_session"

def make_jwt(user):
    now = datetime.utcnow()
    payload = {
        "sub": user["email"],
        "name": user.get("name"),
        "picture": user.get("picture"),
        "iss": "aqi-api",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
# arriba, mantené tus imports y el oauth.register como ya lo tenías

@router.get("/google/login")
async def google_login(request: Request):
    # genera la redirect_uri basada en la request real
    redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")


    # Creamos nuestro JWT de sesión y lo mandamos como cookie HttpOnly
    app_jwt = make_jwt({
        "email": userinfo["email"],
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    })

    resp = RedirectResponse(url=f"{FRONTEND_ORIGIN}/")
    # Cookie segura; en dev Secure=False si no usás https
    resp.set_cookie(
        key=SESSION_COOKIE,
        value=app_jwt,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * JWT_EXPIRES_MIN,
        path="/",
    )
    return resp

@router.post("/logout")
async def logout():
    resp = Response(status_code=204)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp

@router.get("/me")
async def me(request: Request):
    # extrae cookie y valida
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"email": data["sub"], "name": data.get("name"), "picture": data.get("picture")}
    except Exception:
        raise HTTPException(status_code=401, detail="Sesión inválida o expirada")
