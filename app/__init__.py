from flask import Flask
from app.routes.home import home_bp
from app.routes.tracks import tracks_bp
from app.routes.standings import standings_bp
from app.routes.ml import ml_bp
from app.routes.train import train_bp
from app.routes.about import about_bp
from metadata.track_metadata import TRACK_METADATA

def create_app():
    app = Flask(__name__)
    app.secret_key = "7EDYZ8pak3Px"
    app.config['TIMEOUT'] = 600

    # Context processor for global template variables
    @app.context_processor
    def inject_tracks():
        tracklist = [{"id": key, **track} for key, track in TRACK_METADATA.items()]
        return dict(tracks=tracklist)

    app.register_blueprint(home_bp)
    app.register_blueprint(tracks_bp, url_prefix="/tracks")
    app.register_blueprint(standings_bp)
    app.register_blueprint(ml_bp, url_prefix="/ml")
    app.register_blueprint(train_bp, url_prefix="/train")
    app.register_blueprint(about_bp, url_prefix="/about")

    return app
