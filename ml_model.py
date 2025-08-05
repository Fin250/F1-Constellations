import os
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

RESULTS_PATH = 'ml_results.json'


def train_and_predict_all():
    print("Training and predicting for all 2023 rounds...")

    if not os.path.exists('f1_dataset.csv'):
        print("ERROR: Dataset file 'f1_dataset.csv' not found.")
        return []

    data = pd.read_csv('f1_dataset.csv')
    print(f"Dataset loaded: {data.shape[0]} rows, {data.shape[1]} columns")

    df = data.copy()

    # Check required columns
    required_columns = {'season', 'round', 'driver', 'podium'}
    if not required_columns.issubset(df.columns):
        print(f"ERROR: Dataset missing one or more required columns: {required_columns}")
        return []

    train = df[df.season < 2023]
    test_2023 = df[df.season == 2023]

    if train.empty or test_2023.empty:
        print("ERROR: Insufficient data for training or testing")
        return []

    X_train = train.drop(['driver', 'podium'], axis=1)
    y_train = train.podium

    print(f"Training samples: {X_train.shape[0]}, Features: {X_train.shape[1]}")

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train), columns=X_train.columns)

    model = LogisticRegression(solver='lbfgs', max_iter=500)
    model.fit(X_train_scaled, y_train)
    print("Model training completed.")

    all_predictions = []
    unique_rounds = sorted(test_2023['round'].unique())
    print(f"Rounds to predict: {unique_rounds}")

    for circuit in unique_rounds:
        print(f"Predicting for round {circuit}...")
        test = test_2023[test_2023['round'] == circuit]
        X_test = test.drop(['driver', 'podium'], axis=1)

        if X_test.empty:
            print(f"Warning: No test data for round {circuit}")
            continue

        X_test_scaled = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)

        probabilities = model.predict_proba(X_test_scaled)[:, 1]
        prediction_df = pd.DataFrame({'probability': probabilities, 'driver': test['driver']})

        # Ranking
        prediction_df['predicted'] = prediction_df['probability'].rank(ascending=False, method='first')
        prediction_df['predicted'] += np.random.uniform(0, 1e-6, size=len(prediction_df))
        prediction_df.sort_values('predicted', inplace=True)
        prediction_df['predicted'] = prediction_df.groupby('predicted').ngroup() + 1

        prediction_df['round'] = int(circuit)
        prediction_df['probability'] = (prediction_df['probability'] * 100).round(2)

        round_results = prediction_df.sort_values(by='predicted')[['round', 'driver', 'probability']].to_dict(orient='records')
        all_predictions.append({'round': int(circuit), 'predictions': round_results})

    with open(RESULTS_PATH, 'w') as f:
        json.dump(all_predictions, f, indent=2)
        print(f"Predictions saved to {RESULTS_PATH}")

    print("All predictions completed.")
    return all_predictions


def load_predictions():
    print("Loading stored predictions...")
    if not os.path.exists(RESULTS_PATH):
        print("No saved prediction file found.")
        return None
    with open(RESULTS_PATH, 'r') as f:
        try:
            data = json.load(f)
            print(f"Loaded {len(data)} rounds from predictions file.")
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None


def get_predictions_for_round(round_num):
    print(f"Fetching predictions for round {round_num}")
    all_data = load_predictions()
    if all_data is None:
        print("No predictions available.")
        return None

    for round_entry in all_data:
        if round_entry['round'] == round_num:
            print(f"Found predictions for round {round_num}")
            return round_entry['predictions']

    print(f"Predictions for round {round_num} not found.")
    return None
