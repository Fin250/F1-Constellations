import re
import json
from flask import Blueprint, Response

from ml.gp_predictor import RESULTS_PATH_GP
from metadata.driver_metadata import DRIVER_METADATA

standings_bp = Blueprint("standings", __name__, url_prefix="/ml")

def canonical_driver_id(raw_name):

    if not raw_name:
        return None
    raw = str(raw_name).strip()
    lower = raw.lower()

    if lower in DRIVER_METADATA:
        return lower

    sanitized = re.sub(r'[^a-z0-9_]+', '_', lower).strip('_')
    if sanitized in DRIVER_METADATA:
        return sanitized

    for k, v in DRIVER_METADATA.items():
        full = v.get('full_name', '')
        if isinstance(full, str) and full.lower() == lower:
            return k

    for k in DRIVER_METADATA.keys():
        if k.replace('_', ' ').lower() == lower:
            return k

    return sanitized or lower

# Get season standings
@standings_bp.route("/standings/<int:season>")
def get_ml_standings(season):
    print(f"Fetching standings for season: {season}")

    # Load GP results
    try:
        with open(RESULTS_PATH_GP, 'r') as f:
            gp_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading GP results: {e}")
        return Response(response='[]', status=500, mimetype='application/json')

    # Find the requested season
    season_data = next((s for s in gp_data if int(s.get("season", -1)) == season), None)
    if not season_data:
        print(f"No data for requested season {season}")
        return Response(response='[]', status=404, mimetype='application/json')

    season_results = season_data.get("rounds", [])
    if not season_results:
        return Response(response='[]', status=404, mimetype='application/json')

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
    driver_constructors = {}

    for race_idx, race in enumerate(season_results):
        predictions = race.get("predictions", [])
        sorted_preds = sorted(predictions, key=lambda x: float(x.get("probability", 0)), reverse=True)

        for i, pred in enumerate(sorted_preds):
            raw_driver = pred.get("driver")
            if not raw_driver:
                continue

            driver_id = canonical_driver_id(raw_driver)

            constructor = pred.get("constructor")
            if constructor:
                driver_constructors[driver_id] = constructor

            # Podiums
            if i == 0:
                driver_firsts[driver_id] = driver_firsts.get(driver_id, 0) + 1
                if constructor:
                    constructor_firsts[constructor] = constructor_firsts.get(constructor, 0) + 1
            elif i == 1:
                driver_seconds[driver_id] = driver_seconds.get(driver_id, 0) + 1
                if constructor:
                    constructor_seconds[constructor] = constructor_seconds.get(constructor, 0) + 1
            elif i == 2:
                driver_thirds[driver_id] = driver_thirds.get(driver_id, 0) + 1
                if constructor:
                    constructor_thirds[constructor] = constructor_thirds.get(constructor, 0) + 1

            pts = f1_points[i] if i < len(f1_points) else 0
            driver_points[driver_id] = driver_points.get(driver_id, 0) + pts
            if constructor:
                constructor_points[constructor] = constructor_points.get(constructor, 0) + pts

            finish_pos = i + 1
            driver_finishes.setdefault(driver_id, []).append(finish_pos)
            if constructor:
                constructor_finishes.setdefault(constructor, []).append(finish_pos)

    # Sort drivers with tiebreaks
    def driver_sort_key(item):
        driver, points = item
        finishes = sorted(driver_finishes.get(driver, []))
        key = [-points]
        for pos in sorted(set(finishes)):
            key.extend([pos, -finishes.count(pos)])

        max_len = 40
        while len(key) < max_len:
            key.append(999)

        key.append(driver.lower())
        return tuple(key)

    driver_standings = sorted(driver_points.items(), key=driver_sort_key)

    # Sort constructors with tiebreaks
    def constructor_sort_key(item):
        constructor, points = item
        finishes = sorted(constructor_finishes.get(constructor, []))
        key = [-points]
        for pos in sorted(set(finishes)):
            key.extend([pos, -finishes.count(pos)])

        max_len = 40
        while len(key) < max_len:
            key.append(999)

        key.append(constructor.lower())
        return tuple(key)

    constructor_standings = sorted(constructor_points.items(), key=constructor_sort_key)

    # Prepare podium data
    driver_standings_with_podiums = [
        (driver, points, driver_firsts.get(driver, 0), driver_seconds.get(driver, 0), driver_thirds.get(driver, 0))
        for driver, points in driver_standings
    ]

    constructor_standings_with_podiums = [
        (constructor, points, constructor_firsts.get(constructor, 0), constructor_seconds.get(constructor, 0), constructor_thirds.get(constructor, 0))
        for constructor, points in constructor_standings
    ]

    # Build response
    response_data = {
        "driver_standings": [
            {
                "position": i + 1,
                "driver_id": d,
                "driver": DRIVER_METADATA.get(d, {}).get("full_name", d),
                "firsts": firsts,
                "seconds": seconds,
                "thirds": thirds,
                "points": pts,
                "constructor": driver_constructors.get(d),
                "nationality": DRIVER_METADATA.get(d, {}).get("nationality", None),
                "image": f"/static/images/drivers/{d}.png",
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