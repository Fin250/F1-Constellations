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

from flask_sqlalchemy import SQLAlchemy
from jinja2.exceptions import TemplateNotFound

import json
from ml_model import (
    predict_driver_strengths,
    predict_constructor_strengths,
    predict_gp_results,
    RESULTS_PATH_DRIVERS,
    RESULTS_PATH_CONSTRUCTORS,
    RESULTS_PATH_GP
)

from track_metadata import TRACK_METADATA
from driver_metadata import DRIVER_METADATA


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

# Get predictions for a given round
@app.route('/ml/<int:roundnum>')
def get_ml_predictions(roundnum):
    try:
        with open(RESULTS_PATH_GP, 'r') as f:
            gp_results = json.load(f)
        with open(RESULTS_PATH_DRIVERS, 'r') as f:
            driver_strengths = json.load(f)
        with open(RESULTS_PATH_CONSTRUCTORS, 'r') as f:
            constructor_strengths = json.load(f)
    except FileNotFoundError:
        return Response(response='[]', status=404, mimetype='application/json')

    # Filter gp_results and constructor_strengths by roundnum
    gp_result_for_round = next((r for r in gp_results if r["round"] == roundnum), None)
    if not gp_result_for_round:
        return Response(response='[]', status=404, mimetype='application/json')

    # Filter constructor_strengths to only include entries for the given round
    constructor_strengths_for_round = [
        cs for cs in constructor_strengths if cs.get("round") == roundnum
    ]

    response_data = {
        "gp_results": gp_result_for_round,
        "driver_strength": driver_strengths,
        "constructor_strength": constructor_strengths_for_round,
        "driver_metadata": DRIVER_METADATA
    }

    return Response(response=json.dumps(response_data), status=200, mimetype='application/json')

# Manual trigger to rerun the model
@app.route('/ml/train')
def run_ml_training():
    driver_strengths = predict_driver_strengths()
    constructor_strengths = predict_constructor_strengths()
    gp_results = predict_gp_results()
    return Response(response=json.dumps({
        "driver_strengths": driver_strengths,
        "constructor_strengths": constructor_strengths,
        "gp_results": gp_results
    }, indent=2), status=200, mimetype='application/json')

# Run Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)