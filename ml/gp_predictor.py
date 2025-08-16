import json
import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_PATH_GP = os.path.join(BASE_DIR, "gp_predictions.json")
FINAL_DF_PATH = os.path.join(BASE_DIR, "final_df.csv")

# =======================
# GP RESULTS PREDICTION
# =======================
def predict_gp_results():
    print("Training and predicting GP results...")
    df = pd.read_csv(FINAL_DF_PATH)
    train = df[df.season < 2024]
    test = df[df.season == 2024]

    X_train = train.drop(['driver', 'podium'], axis=1).select_dtypes(include=[np.number])
    y_train = train.podium

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(max_iter=500)
    model.fit(X_train_scaled, y_train)

    results = []
    for rnd in sorted(test['round'].unique()):
        test_rnd = test[test['round'] == rnd]
        X_test_rnd = scaler.transform(test_rnd[X_train.columns])
        probabilities = model.predict_proba(X_test_rnd)[:, 1]
        prediction_df = pd.DataFrame({'driver': test_rnd['driver'], 'probability': probabilities})
        prediction_df['probability'] = (prediction_df['probability'] * 100).round(2)
        prediction_df.sort_values('probability', ascending=False, inplace=True)
        results.append({"round": int(rnd), "predictions": prediction_df.to_dict(orient="records")})

    with open(RESULTS_PATH_GP, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"GP results saved to {RESULTS_PATH_GP}")
    return results