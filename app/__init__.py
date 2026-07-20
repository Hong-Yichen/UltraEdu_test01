import os

from flask import Flask

from app.config import CONFIG_MAP
from app.extensions import db, login_manager, migrate, csrf


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(CONFIG_MAP[config_name])

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import models  # noqa: F401  ensures models are registered before migrate/create_all

    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.teacher import teacher_bp
    from app.blueprints.student import student_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(api_bp)

    from app.errors import register_error_handlers

    register_error_handlers(app)

    @app.template_filter("label")
    def label_filter(value):
        """Renders a snake_case enum/choice value as a title-cased display label."""
        if not value:
            return ""
        return str(value).replace("_", " ").title()

    from app.cli import register_cli

    register_cli(app)

    return app
