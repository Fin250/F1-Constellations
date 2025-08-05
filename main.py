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
        get_gp_results,
        train_and_predict_all,
        get_driver_strengths,
        get_constructor_strengths
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

# ML JSON API for frontend
@app.route('/ml/<int:roundnum>')
def get_ml_predictions(roundnum):
    gp_result = get_gp_results(roundnum)
    driver_strengths = get_driver_strengths(roundnum)
    constructor_strengths = get_constructor_strengths(roundnum)

    if gp_result is None:
        print(f"No predictions found for round {roundnum}, running training...")
        train_and_predict_all()
        gp_result = get_gp_results(roundnum)

    if gp_result is None:
        print(f"Still no predictions found after training for round {roundnum}")
        return Response(response='[]', status=404, mimetype='application/json')

    response_data = {
        "gp_results": gp_result,
        "driver_strength": driver_strengths,
        "constructor_strength": constructor_strengths,
        "driver_metadata": DRIVER_METADATA
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