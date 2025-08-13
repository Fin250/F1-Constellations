import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from lightgbm import LGBMRegressor

RESULTS_PATH_DRIVERS = 'driver_strengths.json'
RESULTS_PATH_CONSTRUCTORS = 'constructor_strengths.json'
RESULTS_PATH_GP = 'gp_predictions.json'


# =========================
# DRIVER STRENGTH PREDICTION
# =========================
def predict_driver_strengths():
    print("Calculating driver strengths for 2024 (per-round, drivers present in each round)...")
    df = pd.read_csv("final_df.csv")
    if df.empty:
        print("final_df.csv empty — aborting.")
        return []

    # --- Ensure circuit_id exists (build from boolean one-hot if necessary) ---
    if 'circuit_id' not in df.columns:
        circuit_onehots = [c for c in df.columns if c.startswith('circuit_id_')]
        if circuit_onehots:
            valid = []
            for c in circuit_onehots:
                vals = df[c].dropna().unique()
                try:
                    is_bin = all(v in (0, 1, 0.0, 1.0, True, False) for v in vals)
                except Exception:
                    is_bin = False
                if is_bin:
                    valid.append(c)
            if not valid:
                raise RuntimeError("Found circuit_id_* columns but none look binary. Aborting.")
            mask = (df[valid] == 1)
            idx = mask.idxmax(axis=1)
            no_true = mask.sum(axis=1) == 0
            idx[no_true] = np.nan
            df['circuit_id'] = idx.str.replace('circuit_id_', '', regex=False)
        elif 'circuit' in df.columns:
            df['circuit_id'] = df['circuit'].astype(str)
        else:
            raise RuntimeError("No circuit identifier found in final_df (need 'circuit_id' or circuit_id_*).")

    df['circuit_id'] = df['circuit_id'].astype(object)

    df_2024 = df[df['season'] == 2024].copy()
    drivers_2024 = sorted(df_2024['driver'].dropna().unique())
    rounds_2024 = sorted(df_2024['round'].dropna().unique())

    if len(drivers_2024) == 0 or len(rounds_2024) == 0:
        print("No drivers or rounds for 2024 found in final_df.csv; aborting.")
        return []

    hist = df[(df['season'] < 2024) & (df['driver'].isin(drivers_2024))].copy()

    for col in ['podium', 'grid', 'driver_points']:
        if col not in hist.columns:
            hist[col] = np.nan
    hist['podium'] = pd.to_numeric(hist['podium'], errors='coerce')
    hist['grid'] = pd.to_numeric(hist['grid'], errors='coerce')
    hist['driver_points'] = pd.to_numeric(hist.get('driver_points', 0)).fillna(0.0)

    hist['podium_top3'] = (hist['podium'] <= 3).astype(float)
    hist['win_flag'] = (hist['podium'] == 1).astype(float)
    SEASON_DECAY = 0.5
    if not hist.empty:
        ref_season = int(hist['season'].max())
        hist['season_weight'] = np.exp(-SEASON_DECAY * (ref_season - hist['season']))
    else:
        hist['season_weight'] = pd.Series(dtype=float)

    def wavg(vals, weights):
        vals = np.array(vals, dtype=float)
        weights = np.array(weights, dtype=float)
        mask = ~np.isnan(vals)
        if mask.sum() == 0 or weights[mask].sum() == 0:
            return np.nan
        return (vals[mask] * weights[mask]).sum() / weights[mask].sum()

    track_records = []
    if not hist.empty:
        for (driver, circuit), sub in hist.groupby(['driver', 'circuit_id'], dropna=False):
            if pd.isna(driver) or pd.isna(circuit):
                continue
            w = sub['season_weight'].fillna(1.0)
            track_records.append({
                'driver': driver,
                'circuit_id': str(circuit),
                'race_count': int(len(sub)),
                'avg_finish': wavg(sub['podium'], w),
                'avg_grid': wavg(sub['grid'], w),
                'podium_rate': wavg(sub['podium_top3'], w),
                'win_rate': wavg(sub['win_flag'], w),
                'pts_per_race': wavg(sub['driver_points'], w)
            })
    perf = pd.DataFrame(track_records)

    career_records = []
    if not hist.empty:
        for driver, sub in hist.groupby('driver'):
            w = sub['season_weight'].fillna(1.0)
            career_records.append({
                'driver': driver,
                'career_race_count': int(len(sub)),
                'career_avg_finish': wavg(sub['podium'], w),
                'career_avg_grid': wavg(sub['grid'], w),
                'career_podium_rate': wavg(sub['podium_top3'], w),
                'career_win_rate': wavg(sub['win_flag'], w),
                'career_pts_per_race': wavg(sub['driver_points'], w)
            })
    career = pd.DataFrame(career_records)

    if career.empty:
        career = pd.DataFrame([{
            'driver': d,
            'career_race_count': 0,
            'career_avg_finish': np.nan,
            'career_avg_grid': np.nan,
            'career_podium_rate': np.nan,
            'career_win_rate': np.nan,
            'career_pts_per_race': np.nan
        } for d in drivers_2024])

    if perf.empty:
        perf = pd.DataFrame([{'driver': d, 'circuit_id': None, 'race_count': 0,
                              'avg_finish': np.nan, 'avg_grid': np.nan,
                              'podium_rate': np.nan, 'win_rate': np.nan, 'pts_per_race': np.nan}
                             for d in drivers_2024])
    perf = perf.merge(career, on='driver', how='left')

    def minmax(series, fillna_val=0.5):
        s = pd.Series(series).astype(float)
        if s.isnull().all():
            return pd.Series(fillna_val, index=s.index)
        s = s.fillna(s.median())
        mn, mx = s.min(), s.max()
        if np.isclose(mx, mn):
            return pd.Series(0.5, index=s.index)
        return (s - mn) / (mx - mn)

    finish_score = 1.0 - minmax(perf.get('avg_finish', pd.Series(dtype=float)))
    grid_score = 1.0 - minmax(perf.get('avg_grid', pd.Series(dtype=float)))
    podium_score = minmax(perf.get('podium_rate', pd.Series(dtype=float)))
    win_score = minmax(perf.get('win_rate', pd.Series(dtype=float)))
    pts_score = minmax(perf.get('pts_per_race', pd.Series(dtype=float)))

    perf['track_raw_score'] = (
        0.35 * finish_score +
        0.30 * podium_score +
        0.15 * win_score +
        0.10 * pts_score +
        0.10 * grid_score
    )

    career_tmp = career.copy()
    c_finish = 1.0 - minmax(career_tmp.get('career_avg_finish', pd.Series(dtype=float)))
    c_grid = 1.0 - minmax(career_tmp.get('career_avg_grid', pd.Series(dtype=float)))
    c_podium = minmax(career_tmp.get('career_podium_rate', pd.Series(dtype=float)))
    c_win = minmax(career_tmp.get('career_win_rate', pd.Series(dtype=float)))
    c_pts = minmax(career_tmp.get('career_pts_per_race', pd.Series(dtype=float)))
    career_tmp['career_score'] = (
        0.35 * c_finish + 0.30 * c_podium + 0.15 * c_win + 0.10 * c_pts + 0.10 * c_grid
    )
    perf = perf.merge(career_tmp[['driver', 'career_score', 'career_race_count']], on='driver', how='left')

    PRIOR_COUNT = 5.0
    perf['n'] = perf['race_count'].fillna(0).astype(float)
    perf['k'] = float(PRIOR_COUNT)
    tr_mean = perf['track_raw_score'].mean() if 'track_raw_score' in perf else 0.5
    cs_mean = perf['career_score'].mean() if 'career_score' in perf else 0.5
    perf['combined_score'] = (
        perf['n'] * perf['track_raw_score'].fillna(tr_mean) +
        perf['k'] * perf['career_score'].fillna(cs_mean)
    ) / (perf['n'] + perf['k'])
    perf['combined_score'] = perf['combined_score'].fillna(perf['combined_score'].mean())

    perf['combined_score_clipped'] = perf['combined_score'].clip(0.0, 1.0)
    perf['rating'] = (50.0 + 50.0 * perf['combined_score_clipped']).round(1)

    circuit_round_map = {}
    for rnd in rounds_2024:
        circuits = df_2024.loc[df_2024['round'] == rnd, 'circuit_id'].dropna().unique()
        circuit_round_map[int(rnd)] = str(circuits[0]) if len(circuits) > 0 else None

    out_records = []
    if not perf.empty:
        perf_lookup = perf.set_index(['driver', 'circuit_id'])
    else:
        perf_lookup = None
    career_lookup = career_tmp.set_index('driver') if not career_tmp.empty else pd.DataFrame()

    UNKNOWN_DRIVER_START_RATING = 55.0

    for rnd in rounds_2024:
        circuit_id = circuit_round_map.get(int(rnd))
        drivers_this_round = sorted(df_2024.loc[df_2024['round'] == rnd, 'driver'].dropna().unique())
        if len(drivers_this_round) == 0:
            continue
        for driver in drivers_this_round:
            rating = None
            race_count = 0
            career_score = None
            combined_score = None

            found_track_row = None
            if perf_lookup is not None and circuit_id is not None:
                try:
                    row = perf_lookup.loc[(driver, str(circuit_id))]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    found_track_row = row
                except KeyError:
                    found_track_row = None
                except Exception:
                    found_track_row = None

            if found_track_row is not None:
                r = found_track_row
                rating = float(r.get('rating', (50.0 + 50.0 * cs_mean)))
                race_count = int(r.get('race_count', 0) if not pd.isna(r.get('race_count', 0)) else 0)
                career_score = float(r.get('career_score', cs_mean))
                combined_score = float(r.get('combined_score', career_score if career_score is not None else cs_mean))
            else:
                if driver in career_lookup.index:
                    crow = career_lookup.loc[driver]
                    career_score = float(crow.get('career_score', cs_mean) if not pd.isna(crow.get('career_score', np.nan)) else cs_mean)
                    combined_score = career_score
                    rating = float(round(50.0 + 50.0 * min(max(career_score, 0.0), 1.0), 1))
                    race_count = int(crow.get('career_race_count', 0) if not pd.isna(crow.get('career_race_count', 0)) else 0)
                else:
                    career_score = float(cs_mean)
                    combined_score = career_score
                    rating = float(UNKNOWN_DRIVER_START_RATING)
                    race_count = 0

            out_records.append({
                "season": 2024,
                "round": int(rnd),
                "driver": driver,
                "rating": float(round(float(rating), 1)),
                "race_count": int(race_count),
                "career_score": float(career_score),
                "combined_score": float(combined_score)
            })

    with open(RESULTS_PATH_DRIVERS, 'w') as f:
        json.dump(out_records, f, indent=2)

    print(f"Driver strengths saved to {RESULTS_PATH_DRIVERS} (rows: {len(out_records)})")
    return out_records

# =============================
# CONSTRUCTOR STRENGTH PREDICTION
# =============================
def predict_constructor_strengths():
    print("Training and predicting constructor strengths...")

    df = pd.read_csv("final_df.csv")

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

    train_df = feature_df[feature_df['season'] < 2024].copy()
    if train_df.empty:
        raise RuntimeError("No training data before 2024 found.")

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

    teams_2024 = df.loc[df['season'] == 2024, 'TEAM'].dropna().unique()
    rounds_2024 = sorted(df.loc[df['season'] == 2024, 'round'].unique())

    results_2024 = []

    for rnd in rounds_2024:
        rows = []
        round_circuits = season_round_team_circuit[
            (season_round_team_circuit['season'] == 2024) & (season_round_team_circuit['round'] == rnd)
        ]['circuit'].dropna().unique()
        round_circuit = round_circuits[0] if len(round_circuits) > 0 else 'unknown'

        for team in teams_2024:
            rf = rolling_form(team, 2024, rnd)
            ts = track_strength(team, round_circuit, 2024, rnd)
            rows.append({
                'season': 2024,
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

        actuals = constructor_round_strength[
            (constructor_round_strength['season'] == 2024) &
            (constructor_round_strength['round'] == rnd)
        ][['TEAM','strength']].set_index('TEAM')['strength'].to_dict()

        rnd_df['actual_strength'] = rnd_df['TEAM'].map(actuals).astype(float)

        print(f"Predictions for round {rnd} (2024):")
        print(rnd_df[['TEAM','predicted_strength','actual_strength']].sort_values('predicted_strength', ascending=False).head(15).to_string(index=False))

        results_2024.append(rnd_df[['season', 'round', 'TEAM', 'predicted_strength', 'actual_strength']])

    results_2024_df = pd.concat(results_2024, ignore_index=True)

    results_2024_df.to_json("constructor_strengths.json", orient="records", indent=2)
    print("Constructor strengths per round saved.")

    return results_2024_df.to_dict(orient="records")


# =======================
# GP RESULTS PREDICTION
# =======================
def predict_gp_results():
    print("Training and predicting GP results...")
    df = pd.read_csv("final_df.csv")
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
