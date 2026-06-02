from app import create_app
from app.config import get_settings


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    app.run(
        host=settings.flask_host,
        port=settings.flask_port,
        debug=settings.flask_debug,
    )
