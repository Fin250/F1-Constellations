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
import pandas as pd
import os

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

CURRENT_SEASON = 2024
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DF_PATH = os.path.join(BASE_DIR, "ml", "final_df.csv")
SEASON_COMPLETE = -1

try:
    _FINAL_DF = pd.read_csv(FINAL_DF_PATH)
except Exception:
    _FINAL_DF = pd.DataFrame()

def available_seasons():
    if _FINAL_DF.empty:
        return []
    return sorted(_FINAL_DF['season'].dropna().astype(int).unique().tolist())

def circuit_key_from_row(row):
    if row is None or row.empty:
        return None
    for col in row.index:
        if col.startswith('circuit_id_') and pd.notna(row[col]) and int(row[col]) == 1:
            return col.replace('circuit_id_', '')
    return None

def build_track_from_key(key, round_num=None):
    meta = TRACK_METADATA.get(key, {})
    return {
        "id": key,
        "display_name": meta.get("display_name", key.replace('_', ' ').title()),
        "layout": meta.get("layout", ""),
        "flag": meta.get("flag", ""),
        "detailed_flag": meta.get("detailed_flag", ""),
        "annotated_layout": meta.get("annotated_layout", ""),
        "detailed_track_image": meta.get("detailed_track_image", ""),
        "detailed_track_attribution": meta.get("detailed_track_attribution", ""),
        "round": int(round_num) if round_num is not None else meta.get("round"),
        "wiki": meta.get("wiki", ""),
        "date": meta.get("date", "")
    }

# build tracklist for a past season from final_df
def get_tracks_from_df_for_season(year: int):
    if _FINAL_DF.empty:
        return []

    df_year = _FINAL_DF[_FINAL_DF['season'] == int(year)]
    if df_year.empty:
        return []

    if 'round' in df_year.columns:
        df_year = df_year.sort_values('round').drop_duplicates(subset=['round'])
    else:
        df_year = df_year.reset_index(drop=True)

    tracks = []

    for _, row in df_year.iterrows():
        try:
            round_num = int(row['round'])
        except (TypeError, ValueError):
            continue

        key = None
        for track_key, meta in TRACK_METADATA.items():
            circuit_col = meta.get("circuit_id")
            if isinstance(circuit_col, str) and circuit_col in row.index:
                val = row[circuit_col]
                if pd.notna(val) and int(val) == 1:
                    key = track_key
                    break

        if key:
            t = build_track_from_key(key, round_num)
            tracks.append(t)
        else:
            found = None
            for k, v in TRACK_METADATA.items():
                if v.get('round') == round_num:
                    found = build_track_from_key(k, round_num)
                    break
            if found:
                tracks.append(found)
            else:
                tracks.append({
                    "id": f"round-{round_num}",
                    "display_name": f"Round {round_num}",
                    "layout": "",
                    "flag": "",
                    "detailed_flag": "",
                    "round": round_num,
                    "wiki": "",
                    "date": ""
                })

    return tracks

def get_placeholder_current_season_tracks():
    tracklist = []
    for key, meta in TRACK_METADATA.items():
        t = build_track_from_key(key, meta.get('round'))
        tracklist.append(t)
    tracklist.sort(key=lambda x: (x.get('round') if x.get('round') is not None else 999))
    return tracklist

def get_next_track():
    return 16  # hardcoded next round

# Homepage route
@app.route('/')
def homepage_root():
    return redirect(url_for('homepage_year', year=CURRENT_SEASON))

@app.route('/<int:year>')
def homepage_year(year):
    year = int(year)
    seasons = available_seasons()

    if year in seasons and year < CURRENT_SEASON:
        tracks = get_tracks_from_df_for_season(year)
        next_round = SEASON_COMPLETE
    else:
        tracks = get_placeholder_current_season_tracks()
        next_round = get_next_track() if year == CURRENT_SEASON else None

    return render_template(
        "homepage.html",
        tracks=tracks,
        next_round=next_round,
        year=year,
        seasons=seasons
    )

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
    tracklist = []
    for key, track in TRACK_METADATA.items():
        tracklist.append({"id": key, **track})

    return render_template("about.html", tracks = tracklist)

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
    driver_firsts = {}
    driver_seconds = {}
    driver_thirds = {}
    driver_finishes = {}
    constructor_points = {}
    constructor_firsts = {}
    constructor_seconds = {}
    constructor_thirds = {}
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

            # Winner
            if i == 0:
                driver_firsts[driver] = driver_firsts.get(driver, 0) + 1
                if constructor:
                    constructor_firsts[constructor] = constructor_firsts.get(constructor, 0) + 1

            # Second
            if i == 1:
                driver_seconds[driver] = driver_seconds.get(driver, 0) + 1
                if constructor:
                    constructor_seconds[constructor] = constructor_seconds.get(constructor, 0) + 1
            
            # Third
            if i == 2:
                driver_thirds[driver] = driver_thirds.get(driver, 0) + 1
                if constructor:
                    constructor_thirds[constructor] = constructor_thirds.get(constructor, 0) + 1

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

    driver_standings_with_podiums = []
    for driver, points in driver_standings:
        firsts = driver_firsts[driver] if driver in driver_firsts else 0
        seconds = driver_seconds[driver] if driver in driver_seconds else 0
        thirds = driver_thirds[driver] if driver in driver_thirds else 0
        driver_standings_with_podiums.append((driver, points, firsts, seconds, thirds))

    constructor_standings_with_podiums = []
    for constructor, points in constructor_standings:
        firsts = constructor_firsts[constructor] if constructor in constructor_firsts else 0
        seconds = constructor_seconds[constructor] if constructor in constructor_seconds else 0
        thirds = constructor_thirds[constructor] if constructor in constructor_thirds else 0
        constructor_standings_with_podiums.append((constructor, points, firsts, seconds, thirds))
            
    response_data = {
        "driver_standings": [
            {
                "position": i + 1,
                "driver": DRIVER_METADATA.get(d.lower(), {}).get("full_name", d),
                "firsts": firsts,
                "seconds": seconds,
                "thirds": thirds,
                "points": pts,
                "constructor": DRIVER_METADATA.get(d.lower(), {}).get("constructor", None),
                "nationality": DRIVER_METADATA.get(d.lower(), {}).get("nationality", None),
                "image": DRIVER_METADATA.get(d.lower(), {}).get("image", None),
            }
            for i, (d, pts, firsts, seconds, thirds) in enumerate(driver_standings_with_podiums)
        ],
        "constructor_standings": [
            {
                "position": i + 1,
                "constructor": c,
                "firsts": firsts,
                "seconds": seconds,
                "thirds": thirds,
                "points": pts
            }
            for i, (c, pts, firsts, seconds, thirds) in enumerate(constructor_standings_with_podiums)
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