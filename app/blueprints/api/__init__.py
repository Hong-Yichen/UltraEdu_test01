from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

from app.blueprints.api import (  # noqa: E402,F401
    ping,
    uploads,
    notifications,
    canvas,
    ai,
    messages,
    groups,
)
