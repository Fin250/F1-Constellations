import json
from flask import Blueprint, Response

from ml.gp_predictor import RESULTS_PATH_GP
from metadata.driver_metadata import DRIVER_METADATA

standings_bp = Blueprint("standings", __name__, url_prefix="/ml")

# Get season standings
@standings_bp.route("/standings")
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