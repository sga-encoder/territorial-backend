from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db, migrate, socketio


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        allow_headers="*",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    from app.models import all_models  # noqa: F401
    from app.controllers import register_blueprints
    register_blueprints(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
