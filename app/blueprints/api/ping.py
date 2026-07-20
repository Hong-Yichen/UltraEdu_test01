from app.blueprints.api import api_bp


@api_bp.route("/ping")
def ping():
    return {"status": "ok"}
