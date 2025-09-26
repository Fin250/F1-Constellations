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
def predict_gp_results(start_year: int = 2010, end_year: int = 2025):
    print("Training and predicting GP results...")
    df = pd.read_csv(FINAL_DF_PATH)

    constructor_cols = [
        c for c in df.columns 
        if c.startswith("constructor_") 
        and c not in ["constructor_wins", "constructor_points", "constructor_standings_pos"]
    ]

    seasons = sorted([s for s in df['season'].unique() if start_year <= s <= end_year])
    all_results = []

    for season in seasons:
        train = df[df.season < season]
        test = df[df.season == season]

        if train.empty or test.empty:
            continue

        drop_cols = ['driver', 'podium', 'date']
        X_train = train.drop(columns=[c for c in drop_cols if c in train.columns]).select_dtypes(include=[np.number])
        y_train = train.podium

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        model = LogisticRegression(max_iter=500)
        model.fit(X_train_scaled, y_train)

        season_results = {"season": int(season), "rounds": []}

        for rnd in sorted(test['round'].unique()):
            test_rnd = test[test['round'] == rnd]
            X_test_rnd = scaler.transform(test_rnd[X_train.columns])
            probabilities = model.predict_proba(X_test_rnd)[:, 1]

            prediction_records = []
            for idx, row in test_rnd.iterrows():
                constructor = None
                for col in constructor_cols:
                    if int(row[col]) == 1:
                        constructor = col.replace("constructor_", "").replace("_f1", "").replace("_racing", "").capitalize()
                        break

                prediction_records.append({
                    "driver": row['driver'],
                    "constructor": constructor if constructor else "Unknown",
                    "probability": round(float(probabilities[test_rnd.index.get_loc(idx)]) * 100, 2)
                })

            prediction_records.sort(key=lambda x: x['probability'], reverse=True)

            season_results["rounds"].append({
                "round": int(rnd),
                "predictions": prediction_records
            })

        all_results.append(season_results)

    with open(RESULTS_PATH_GP, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"GP results saved to {RESULTS_PATH_GP}")
    return all_results