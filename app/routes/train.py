import json
from flask import Blueprint, Response

from ml.driver_strength_predictor import predict_driver_strengths
from ml.constructor_strength_predictor import predict_constructor_strengths
from ml.gp_predictor import predict_gp_results

train_bp = Blueprint("train", __name__, url_prefix="/ml")

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