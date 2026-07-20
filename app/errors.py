from flask import render_template, request, jsonify


def _wants_json():
    return request.path.startswith("/api/") or request.is_json


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        message = str(e.description or "")
        if _wants_json():
            return jsonify({"error": "bad_request", "description": message}), 400
        return message or "Bad request", 400

    @app.errorhandler(403)
    def forbidden(e):
        message = str(e.description or "")
        if _wants_json():
            return jsonify({"error": "forbidden", "description": message}), 403
        return render_template("errors/403.html", message=message), 403

    @app.errorhandler(404)
    def not_found(e):
        if _wants_json():
            return jsonify({"error": "not_found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        if _wants_json():
            return jsonify({"error": "server_error"}), 500
        return render_template("errors/500.html"), 500
