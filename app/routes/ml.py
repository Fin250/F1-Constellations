import json
import os
import pandas as pd
from flask import Blueprint, Response

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

from metadata.driver_metadata import DRIVER_METADATA

ml_bp = Blueprint("ml", __name__, url_prefix="/ml")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DF_PATH = os.path.join(BASE_DIR, "..", "ml", "final_df.csv")

try:
    _FINAL_DF = pd.read_csv(FINAL_DF_PATH)
except Exception:
    _FINAL_DF = pd.DataFrame()


@ml_bp.route("/<int:season>/<int:roundnum>")
def get_ml_predictions(season, roundnum):
    try:
        with open(RESULTS_PATH_GP, "r") as f:
            gp_results_all = json.load(f)
        with open(RESULTS_PATH_DRIVERS, "r") as f:
            driver_strengths_all = json.load(f)
        with open(RESULTS_PATH_CONSTRUCTORS, "r") as f:
            constructor_strengths_all = json.load(f)
    except FileNotFoundError:
        driver_strengths_all = predict_driver_strengths()
        constructor_strengths_all = predict_constructor_strengths()
        gp_results_all = predict_gp_results()

        with open(RESULTS_PATH_GP, "w") as f:
            json.dump(gp_results_all, f, indent=2)
        with open(RESULTS_PATH_DRIVERS, "w") as f:
            json.dump(driver_strengths_all, f, indent=2)
        with open(RESULTS_PATH_CONSTRUCTORS, "w") as f:
            json.dump(constructor_strengths_all, f, indent=2)
    except json.JSONDecodeError:
        return Response(response="[]", status=500, mimetype="application/json")

    gp_result_for_round = next(
        (s for s in gp_results_all if int(s.get("season", -1)) == season), None
    )
    if not gp_result_for_round:
        return Response(response="[]", status=404, mimetype="application/json")

    gp_result_for_round = next(
        (r for r in gp_result_for_round.get("rounds", [])
         if int(r.get("round", -1)) == roundnum),
        None
    )
    if not gp_result_for_round:
        return Response(response="[]", status=404, mimetype="application/json")

    predictions = gp_result_for_round.get("predictions", [])
    drivers_in_round = {p.get("driver") for p in predictions if p.get("driver")}
    drivers_in_round_lower = {d.lower() for d in drivers_in_round}

    driver_strengths_for_round = []
    for season_entry in driver_strengths_all:
        if int(season_entry.get("season", -1)) != season:
            continue
        for rnd_entry in season_entry.get("rounds", []):
            if int(rnd_entry.get("round", -1)) != roundnum:
                continue
            for ds in rnd_entry.get("predictions", []):
                if not drivers_in_round or ds.get("driver", "").lower() in drivers_in_round_lower:
                    driver_strengths_for_round.append(ds)

    if not driver_strengths_for_round and drivers_in_round:
        for d in sorted(drivers_in_round):
            driver_strengths_for_round.append({
                "season": season,
                "round": roundnum,
                "driver": d,
                "rating": 75.0,
                "race_count": 0,
                "career_score": 0.5,
                "combined_score": 0.5,
                "track_raw_score": None,
            })

    constructor_strengths_for_round = []
    for season_entry in constructor_strengths_all:
        if int(season_entry.get("season", -1)) != season:
            continue
        for rnd_entry in season_entry.get("rounds", []):
            if int(rnd_entry.get("round", -1)) != roundnum:
                continue
            constructor_strengths_for_round.extend(rnd_entry.get("predictions", []))

    response_data = {
        "gp_results": gp_result_for_round,
        "driver_strength": driver_strengths_for_round,
        "constructor_strength": constructor_strengths_for_round,
        "driver_metadata": DRIVER_METADATA,
    }

    return Response(
        response=json.dumps(response_data, indent=2),
        status=200,
        mimetype="application/json"
    )
