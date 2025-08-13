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
        round_number=track["round"],
        wiki=track["wiki"],
        f1_website=track["f1_website"]
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
    except FileNotFoundError as e:
        driver_strengths_new = predict_driver_strengths()
        constructor_strengths_new = predict_constructor_strengths()
        gp_results_new = predict_gp_results()

        with open(RESULTS_PATH_GP, 'w') as f:
            json.dump(gp_results_new, f)
        with open(RESULTS_PATH_DRIVERS, 'w') as f:
            json.dump(driver_strengths_new, f)
        with open(RESULTS_PATH_CONSTRUCTORS, 'w') as f:
            json.dump(constructor_strengths_new, f)

        gp_results, driver_strengths, constructor_strengths = (
            gp_results_new, driver_strengths_new, constructor_strengths_new
        )
    except json.JSONDecodeError as e:
        return Response(response='[]', status=500, mimetype='application/json')

    gp_result_for_round = next((r for r in gp_results if int(r.get("round", -1)) == int(roundnum)), None)
    if not gp_result_for_round:
        return Response(response='[]', status=404, mimetype='application/json')

    try:
        predictions = gp_result_for_round.get("predictions", [])
        drivers_in_round = {p.get("driver") for p in predictions if p.get("driver")}
        drivers_in_round_lower = {d.lower() for d in drivers_in_round}
    except Exception:
        drivers_in_round = set()
        drivers_in_round_lower = set()

    driver_strengths_for_round = []
    for ds in driver_strengths:
        try:
            if int(ds.get("round", -1)) == int(roundnum) and int(ds.get("season", -1)) == 2024:
                driver_name = ds.get("driver")
                if not drivers_in_round:
                    driver_strengths_for_round.append(ds)
                else:
                    if driver_name and driver_name.lower() in drivers_in_round_lower:
                        driver_strengths_for_round.append(ds)
        except Exception:
            continue

    if not driver_strengths_for_round:
        for ds in driver_strengths:
            driver_name = ds.get("driver")
            if driver_name and driver_name.lower() in drivers_in_round_lower:
                driver_strengths_for_round.append(ds)

    if not driver_strengths_for_round:
        for d in sorted(drivers_in_round):
            driver_strengths_for_round.append({
                "season": 2024,
                "round": roundnum,
                "driver": d,
                "rating": 75.0,
                "race_count": 0,
                "career_score": 0.5,
                "combined_score": 0.5
            })

    constructor_strengths_for_round = [
        cs for cs in constructor_strengths
        if int(cs.get("round", -1)) == int(roundnum) and int(cs.get("season", 2024)) == 2024
    ]

    if not constructor_strengths_for_round:
        constructor_strengths_for_round = [
            cs for cs in constructor_strengths
            if int(cs.get("round", -1)) == int(roundnum)
        ]

    response_data = {
        "gp_results": gp_result_for_round,
        "driver_strength": driver_strengths_for_round,
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