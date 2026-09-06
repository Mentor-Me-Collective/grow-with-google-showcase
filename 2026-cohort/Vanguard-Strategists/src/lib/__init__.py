from pathlib import Path
from flask import Flask
from flask_cors import CORS
from lib.config import Config
from lib.extensions import db

def create_app() -> Flask:
    app = Flask(__name__,
                instance_relative_config=True,
                template_folder=str(Path(__file__).parent / "templates"),
                static_folder=str(Path(__file__).parent / "statics"))
    app.config.from_object(Config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    CORS(app)
    register_blueprints(app)
    with app.app_context():
        import lib.models
        db.create_all()
    return app


def register_blueprints(app: Flask) -> None:
    from lib.routes.api_routes import api_routes
    from lib.routes.web_routes import web_routes
    app.register_blueprint(web_routes)
    app.register_blueprint(api_routes, url_prefix="/api")


