import http
from fastapi import APIRouter
from .app.http.controllers.api.v1.app_controller import router as app_router

def get_app_module():
    return app_router