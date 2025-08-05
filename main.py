from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from flask_sqlalchemy import SQLAlchemy
from jinja2.exceptions import TemplateNotFound

import json
from ml_model import train_and_predict_all, get_predictions_for_round, load_predictions
from track_metadata import TRACK_METADATA

# Initialise Flask instance
app = Flask(__name__)
app.config['TIMEOUT'] = 600
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
app.secret_key = '7EDYZ8pak3Px'

# Homepage route
@app.route('/')
def homepage():
    return render_template("/homepage.html")

# Render individual track pages if they exist
@app.route('/tracks/<trackname>')
def tracks(trackname):
    track = TRACK_METADATA.get(trackname)
    if not track:
        return render_template("homepage.html")

    return render_template(
        "track_template.html",
        track_display_name=track["display_name"],
        annotated_layout_path=f"/static/images/annotated-layouts/annotated-{track['layout']}",
        flag_path=f"/static/images/flags/{track['flag']}",
        script_path="/static/scripts/tracks.js",
        round_number=track["round"]
    )

# ML JSON API for frontend
@app.route('/ml/<int:roundnum>')
def get_ml_predictions(roundnum):
    predictions = get_predictions_for_round(roundnum)

    if predictions is None:
        print(f"No predictions found for round {roundnum}, running training...")
        train_and_predict_all()
        predictions = get_predictions_for_round(roundnum)

    if predictions is None:
        print(f"Still no predictions found after training for round {roundnum}")
        return Response(response='[]', status=404, mimetype='application/json')

    placeholder_driver_strength = [
        {"driver": f"Driver {i+1}", "strength": round(100 - i*2.5, 1)} for i in range(20)
    ]

    placeholder_constructor_strength = [
        {"constructor": f"Team {i+1}", "strength": round(100 - i*5, 1)} for i in range(10)
    ]

    response_data = {
        "gp_results": predictions,
        "driver_strength": placeholder_driver_strength,
        "constructor_strength": placeholder_constructor_strength
    }

    return Response(response=json.dumps(response_data), status=200, mimetype='application/json')

# Manual trigger to rerun the model
@app.route('/ml/train')
def run_ml_training():
    train_and_predict_all()
    return 'Model retrained and results saved.', 200

# Run Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)