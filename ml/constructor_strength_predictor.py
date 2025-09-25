import json
import os
import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_PATH_CONSTRUCTORS = os.path.join(BASE_DIR, "constructor_strengths.json")
FINAL_DF_PATH = os.path.join(BASE_DIR, "final_df.csv")

# =============================
# CONSTRUCTOR STRENGTH PREDICTION
# =============================
def predict_constructor_strengths(start_year: int = 2010, end_year: int = 2025):
    print(f"Training and predicting constructor strengths from {start_year} to {end_year}...")

    df = pd.read_csv(FINAL_DF_PATH)

    constructor_cols = [c for c in df.columns if c.startswith("constructor_")]
    onehot_cols = []
    for col in constructor_cols:
        vals = df[col].dropna().unique()
        try:
            is_binary = all((v in (0, 1, 0.0, 1.0, True, False)) for v in vals)
        except Exception:
            is_binary = False
        if is_binary:
            onehot_cols.append(col)

    if not onehot_cols:
        raise RuntimeError("No one-hot constructor columns detected. Aborting — check column names.")

    mask = (df[onehot_cols] == 1)
    idx = mask.idxmax(axis=1)
    no_team_rows = mask.sum(axis=1) == 0
    idx[no_team_rows] = None
    df['TEAM'] = idx.str.replace("constructor_", "", regex=False)
    df = df[df['TEAM'].notna()].copy()

    circuit_cols = [c for c in df.columns if c.startswith("circuit_id_")]
    if not circuit_cols:
        raise RuntimeError("No circuit_id_* columns found.")

    def get_circuit_name(row):
        true_cols = [c for c in circuit_cols if row.get(c, 0) == 1]
        if len(true_cols) == 1:
            return true_cols[0].replace("circuit_id_", "")
        elif len(true_cols) == 0:
            return np.nan
        else:
            return true_cols[0].replace("circuit_id_", "")

    df['circuit'] = df.apply(get_circuit_name, axis=1)

    def compute_constructor_strength(group):
        avg_pos = group["podium"].mean()
        best_pos = group["podium"].min()
        max_points = df["constructor_points"].max() if "constructor_points" in df.columns else 1.0
        points_score = group["constructor_points"].mean() / max_points if max_points != 0 else 0.0
        drivers_in_points = (group["podium"] <= 10).sum()
        both_scored_flag = 1 if drivers_in_points >= 2 else 0
        avg_pos_score = (21 - avg_pos) / 20
        best_pos_score = (21 - best_pos) / 20
        strength = 0.4 * avg_pos_score + 0.3 * best_pos_score + 0.2 * points_score + 0.1 * both_scored_flag
        return pd.Series({
            "avg_pos": avg_pos,
            "best_pos": best_pos,
            "points_score": points_score,
            "both_scored_flag": both_scored_flag,
            "strength": strength
        })

    constructor_round_strength = (
        df.groupby(["season", "round", "TEAM"], dropna=False)
          .apply(compute_constructor_strength)
          .reset_index()
    )

    season_round_team_circuit = (
        df[['season', 'round', 'TEAM', 'circuit']]
        .drop_duplicates()
        .groupby(['season','round','TEAM'], dropna=False)
        .first()
        .reset_index()
    )

    constructor_round_strength = constructor_round_strength.merge(
        season_round_team_circuit,
        on=['season', 'round', 'TEAM'],
        how='left'
    )

    extra_cols = ['weather_warm','weather_cold','weather_dry','weather_wet','weather_cloudy']
    extra_cols = [c for c in extra_cols if c in df.columns]
    cols_to_keep = ['season', 'round', 'TEAM', 'circuit'] + extra_cols

    df_subset = df[cols_to_keep].drop_duplicates(subset=['season','round','TEAM'])
    feature_df = constructor_round_strength.merge(
        df_subset,
        on=['season','round','TEAM','circuit'],
        how='left'
    )

    drop_cols = [
        'driver','podium','driver_points','driver_wins','driver_standings_pos',
        'constructor_points','constructor_wins','constructor_standings_pos',
        'driver_name','driver_age','qualifying_time'
    ]
    drop_cols = [c for c in drop_cols if c in feature_df.columns]
    feature_df = feature_df.drop(columns=drop_cols)

    feature_df['circuit'] = feature_df['circuit'].fillna('unknown').astype(str)
    feature_df['TEAM'] = feature_df['TEAM'].fillna('unknown').astype(str)

    train_df = feature_df[feature_df['season'] < end_year].copy()
    if train_df.empty:
        raise RuntimeError(f"No training data before {end_year} found.")

    X_train = pd.get_dummies(train_df.drop(columns=['strength']), columns=['TEAM', 'circuit'], dtype=float)
    y_train = train_df['strength'].astype(float)

    non_numeric = X_train.select_dtypes(exclude=[np.number]).columns.tolist()
    if non_numeric:
        X_train = X_train.drop(columns=non_numeric)

    model = LGBMRegressor(n_estimators=500, learning_rate=0.05, max_depth=6, random_state=42)
    model.fit(X_train, y_train)

    hist = constructor_round_strength.copy()
    hist['circuit'] = hist['circuit'].fillna('unknown').astype(str)

    SEASON_DECAY = 1.0
    ROUND_DECAY = 0.8

    def rolling_form(team, current_season, current_round):
        past = hist[
            (hist['TEAM'] == team) &
            (
                (hist['season'] < current_season) |
                ((hist['season'] == current_season) & (hist['round'] < current_round))
            )
        ].copy()
        if past.empty:
            return {'avg_pos': np.nan, 'best_pos': np.nan, 'points_score': np.nan, 'both_scored_flag': 0}
        past['season_weight'] = np.exp(-SEASON_DECAY * (current_season - past['season']))
        past['round_weight'] = np.exp(-ROUND_DECAY * (current_round - past['round']))
        past['total_weight'] = past['season_weight'] * past['round_weight']
        return {
            'avg_pos': np.average(past['avg_pos'], weights=past['total_weight']),
            'best_pos': past.loc[past['best_pos'].idxmin(), 'best_pos'],
            'points_score': np.average(past['points_score'], weights=past['total_weight']),
            'both_scored_flag': int(np.average(past['both_scored_flag'], weights=past['total_weight']) > 0.5)
        }

    def track_strength(team, circuit, current_season, current_round):
        past_track = hist[
            (hist['TEAM'] == team) &
            (hist['circuit'] == circuit) &
            (
                (hist['season'] < current_season) |
                ((hist['season'] == current_season) & (hist['round'] < current_round))
            )
        ]
        if past_track.empty:
            return np.nan
        return past_track['strength'].mean()

    # === Loop across seasons ===
    results = []
    for season in range(start_year, end_year + 1):
        teams = df.loc[df['season'] == season, 'TEAM'].dropna().unique()
        rounds = sorted(df.loc[df['season'] == season, 'round'].unique())

        season_results = []
        for rnd in rounds:
            rows = []
            round_circuits = season_round_team_circuit[
                (season_round_team_circuit['season'] == season) & (season_round_team_circuit['round'] == rnd)
            ]['circuit'].dropna().unique()
            round_circuit = round_circuits[0] if len(round_circuits) > 0 else 'unknown'

            for team in teams:
                rf = rolling_form(team, season, rnd)
                ts = track_strength(team, round_circuit, season, rnd)
                rows.append({
                    'season': season,
                    'round': rnd,
                    'TEAM': team,
                    'avg_pos': rf['avg_pos'],
                    'best_pos': rf['best_pos'],
                    'points_score': rf['points_score'],
                    'both_scored_flag': rf['both_scored_flag'],
                    'track_strength': ts,
                    'circuit': round_circuit
                })

            rnd_df = pd.DataFrame(rows)

            for col in ['avg_pos', 'best_pos', 'points_score', 'both_scored_flag', 'track_strength']:
                if col in rnd_df.columns and rnd_df[col].isna().any():
                    median_val = feature_df[col].median() if col in feature_df.columns else 0.0
                    rnd_df[col].fillna(median_val, inplace=True)

            X_round = pd.get_dummies(rnd_df.drop(columns=['season', 'round']), columns=['TEAM', 'circuit'], dtype=float)
            X_round = X_round.reindex(columns=X_train.columns, fill_value=0)

            preds = model.predict(X_round)
            rnd_df['predicted_strength'] = preds

            season_results.append({
                "round": int(rnd),
                "predictions": rnd_df[['TEAM','predicted_strength']].to_dict(orient="records")
            })

        results.append({
            "season": season,
            "rounds": season_results
        })

    with open(RESULTS_PATH_CONSTRUCTORS, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Constructor strengths saved to {RESULTS_PATH_CONSTRUCTORS}")
    return results