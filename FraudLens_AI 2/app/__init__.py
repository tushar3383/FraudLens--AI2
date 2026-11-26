from flask import Flask
from pathlib import Path
from config import Config
from .database import init_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    for key in ("UPLOAD_FOLDER", "REPORT_FOLDER", "INSTANCE_FOLDER"):
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)
    init_db(app.config["DATABASE"])
    from .routes import bp
    app.register_blueprint(bp)
    return app
