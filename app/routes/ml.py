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

CURRENT_SEASON = 2024
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DF_PATH = os.path.join(BASE_DIR, "..", "ml", "final_df.csv")

try:
    _FINAL_DF = pd.read_csv(FINAL_DF_PATH)
except Exception:
    _FINAL_DF = pd.DataFrame()


@ml_bp.route("/<int:roundnum>")
def get_ml_predictions(roundnum):
    try:
        with open(RESULTS_PATH_GP, "r") as f:
            gp_results = json.load(f)
        with open(RESULTS_PATH_DRIVERS, "r") as f:
            driver_strengths = json.load(f)
        with open(RESULTS_PATH_CONSTRUCTORS, "r") as f:
            constructor_strengths = json.load(f)
    except FileNotFoundError:
        driver_strengths_new = predict_driver_strengths()
        constructor_strengths_new = predict_constructor_strengths()
        gp_results_new = predict_gp_results()

        with open(RESULTS_PATH_GP, "w") as f:
            json.dump(gp_results_new, f)
        with open(RESULTS_PATH_DRIVERS, "w") as f:
            json.dump(driver_strengths_new, f)
        with open(RESULTS_PATH_CONSTRUCTORS, "w") as f:
            json.dump(constructor_strengths_new, f)

        gp_results, driver_strengths, constructor_strengths = (
            gp_results_new, driver_strengths_new, constructor_strengths_new
        )
    except json.JSONDecodeError:
        return Response(response="[]", status=500, mimetype="application/json")

    gp_result_for_round = next(
        (r for r in gp_results if int(r.get("round", -1)) == int(roundnum)), None
    )
    if not gp_result_for_round:
        return Response(response="[]", status=404, mimetype="application/json")

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
            if (
                int(ds.get("round", -1)) == int(roundnum)
                and int(ds.get("season", -1)) == CURRENT_SEASON
            ):
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
                "season": CURRENT_SEASON,
                "round": roundnum,
                "driver": d,
                "rating": 75.0,
                "race_count": 0,
                "career_score": 0.5,
                "combined_score": 0.5,
            })

    constructor_strengths_for_round = [
        cs for cs in constructor_strengths
        if int(cs.get("round", -1)) == int(roundnum)
        and int(cs.get("season", CURRENT_SEASON)) == CURRENT_SEASON
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
        "driver_metadata": DRIVER_METADATA,
    }

    return Response(response=json.dumps(response_data), status=200, mimetype="application/json")
