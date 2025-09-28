import json
import os
from flask import Blueprint, Response

from ml.driver_strength_predictor import predict_driver_strengths
from ml.constructor_strength_predictor import predict_constructor_strengths
from ml.gp_predictor import predict_gp_results
from ml.current_season_gen import regenerate_dataframe

train_bp = Blueprint("train", __name__, url_prefix="/ml")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DF_PATH = os.path.join(BASE_DIR, "..", "ml", "final_df.csv")

@train_bp.route("/train")
def run_ml_training():
    driver_strengths = predict_driver_strengths()
    constructor_strengths = predict_constructor_strengths()
    gp_results = predict_gp_results()
    return Response(response=json.dumps({
        "driver_strengths": driver_strengths,
        "constructor_strengths": constructor_strengths,
        "gp_results": gp_results
    }, indent=2), status=200, mimetype='application/json')

@train_bp.route("/df")
def run_current_season_gen():
    try:
        regenerate_dataframe()

        # Retrain ML predictions
        driver_strengths = predict_driver_strengths()
        constructor_strengths = predict_constructor_strengths()
        gp_results = predict_gp_results()

        return Response(
            response=json.dumps({
                "status": "success",
                "message": "Regenerated dataframe and retrained ML predictions",
                "driver_strengths": driver_strengths,
                "constructor_strengths": constructor_strengths,
                "gp_results": gp_results
            }, indent=2),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        return Response(
            response=json.dumps({"status": "error", "message": str(e)}),
            status=500,
            mimetype="application/json"
        )