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

from jinja2.exceptions import TemplateNotFound

import json

from ml.driver_strength_predictor import (
    predict_driver_strengths,
    RESULTS_PATH_DRIVERS,
)
from ml.gp_predictor import (
    predict_gp_results,
    RESULTS_PATH_GP
)
from ml.constructor_strength_predictor import (
    predict_constructor_strengths,
    RESULTS_PATH_CONSTRUCTORS,
)

from metadata.track_metadata import TRACK_METADATA
from metadata.driver_metadata import DRIVER_METADATA


# Initialise Flask instance
app = Flask(__name__)
app.config['TIMEOUT'] = 600
app.secret_key = '7EDYZ8pak3Px'

def get_next_track():
    return 16  # hardcoded next round

# Homepage route
@app.route('/')
def homepage():
    tracklist = []
    for key, track in TRACK_METADATA.items():
        tracklist.append({"id": key, **track})

    next_round = get_next_track()

    return render_template("/homepage.html", tracks = tracklist, next_round=next_round)

# Old homepage route
@app.route('/old')
def old_homepage():
    tracklist = []
    for key, track in TRACK_METADATA.items():
        tracklist.append({"id": key, **track})

    next_round = get_next_track()

    return render_template("/old_homepage.html", tracks = tracklist, next_round=next_round)

# Render individual track pages if they exist
@app.route('/tracks/<trackname>')
def tracks(trackname):
    tracklist = []
    for key, track in TRACK_METADATA.items():
        tracklist.append({"id": key, **track})

    track = TRACK_METADATA.get(trackname)
    if not track:
        return render_template("homepage.html")

    return render_template(
        "track_template.html",
        tracks = tracklist,
        track_display_name=track["display_name"],
        f1_website=track["f1_website"],
        flag_path=f"/static/images/flags/{track['flag']}",
        annotated_layout_path=f"/static/images/annotated-layouts/annotated-{track['annotated_layout']}",
        round_number=track["round"],
        track_image=track["detailed_track_image"],
        track_attribution=track["detailed_track_attribution"],
        wiki=track["wiki"],
    )

# About page
@app.route('/about')
def about():
    return render_template("about.html")

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

# Get season standings
@app.route('/ml/standings')
def get_ml_standings():
    try:
        with open(RESULTS_PATH_GP, 'r') as f:
            gp_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return Response(response='[]', status=500, mimetype='application/json')

    # P1 gets 26 points because of fastest lap
    f1_points = [26, 18, 15, 12, 10, 8, 6, 4, 2, 1]

    driver_points = {}
    driver_finishes = {}
    constructor_points = {}
    constructor_finishes = {}

    for race in gp_results:
        predictions = race.get("predictions", [])
        sorted_preds = sorted(predictions, key=lambda x: float(x.get("probability", 0)), reverse=True)

        for i, pred in enumerate(sorted_preds):
            driver = pred.get("driver")
            if not driver:
                continue
            driver_key = driver.lower()
            constructor = DRIVER_METADATA.get(driver_key, {}).get("constructor")

            pts = f1_points[i] if i < len(f1_points) else 0
            driver_points[driver] = driver_points.get(driver, 0) + pts
            if constructor:
                constructor_points[constructor] = constructor_points.get(constructor, 0) + pts

            finish_pos = i + 1
            driver_finishes.setdefault(driver, []).append(finish_pos)
            if constructor:
                constructor_finishes.setdefault(constructor, []).append(finish_pos)

    # sort drivers with tiebreaks
    def driver_sort_key(item):
        driver, points = item
        finishes = sorted(driver_finishes.get(driver, []))
        key = [-points]
        if finishes:
            for pos in sorted(set(finishes)):
                key.append(pos)
                key.append(-finishes.count(pos))
        return tuple(key + [driver.lower()])

    driver_standings = sorted(driver_points.items(), key=driver_sort_key)

    # sort constructors with tiebreaks
    def constructor_sort_key(item):
        constructor, points = item
        finishes = sorted(constructor_finishes.get(constructor, []))
        key = [-points]
        if finishes:
            for pos in sorted(set(finishes)):
                key.append(pos)
                key.append(-finishes.count(pos))
        return tuple(key + [constructor.lower()])

    constructor_standings = sorted(constructor_points.items(), key=constructor_sort_key)

    response_data = {
        "driver_standings": [
            {
                "position": i + 1,
                "driver": DRIVER_METADATA.get(d.lower(), {}).get("full_name", d),
                "points": pts,
                "constructor": DRIVER_METADATA.get(d.lower(), {}).get("constructor", None),
                "nationality": DRIVER_METADATA.get(d.lower(), {}).get("nationality", None),
                "image": DRIVER_METADATA.get(d.lower(), {}).get("image", None),
            }
            for i, (d, pts) in enumerate(driver_standings)
        ],
        "constructor_standings": [
            {
                "position": i + 1,
                "constructor": c,
                "points": pts
            }
            for i, (c, pts) in enumerate(constructor_standings)
        ]
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