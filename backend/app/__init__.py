from flask import Flask
from flask_cors import CORS

from app.api.routes import api_bp
from app.config import get_settings
from app.utils.responses import error_response


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    CORS(app, origins=settings.cors_origins)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.errorhandler(404)
    def not_found(_error):
        return error_response("resource not found", 404)

    @app.errorhandler(Exception)
    def internal_error(error):
        app.logger.exception("未处理异常: %s", error)
        return error_response("internal server error", 500)

    return app
