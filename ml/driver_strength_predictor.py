import json
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_PATH_DRIVERS = os.path.join(BASE_DIR, "driver_strengths.json")
FINAL_DF_PATH = os.path.join(BASE_DIR, "final_df.csv")

def predict_driver_strengths(start_year: int = 2010, end_year: int = 2024):
    print(f"Calculating driver strengths from {start_year} to {end_year}...")
    df = pd.read_csv(FINAL_DF_PATH)
    if df.empty:
        return []

    # --- Ensure circuit_id exists (build from boolean one-hot if necessary) ---
    if 'circuit_id' not in df.columns:
        circuit_onehots = [c for c in df.columns if c.startswith('circuit_id_')]
        if circuit_onehots:
            mask = (df[circuit_onehots] == 1)
            idx = mask.idxmax(axis=1)
            no_true = mask.sum(axis=1) == 0
            idx[no_true] = np.nan
            df['circuit_id'] = idx.str.replace('circuit_id_', '', regex=False)
        elif 'circuit' in df.columns:
            df['circuit_id'] = df['circuit'].astype(str)
        else:
            raise RuntimeError("No circuit identifier found in final_df (need 'circuit_id' or circuit_id_*).")
    df['circuit_id'] = df['circuit_id'].astype(object)

    # --- Identify valid constructor columns ---
    constructor_cols = [
        c for c in df.columns
        if c.startswith("constructor_") and c not in ["constructor_wins", "constructor_points", "constructor_standings_pos"]
    ]

    # --- Focus dataset on target range ---
    df_target = df[(df['season'] >= start_year) & (df['season'] <= end_year)].copy()
    drivers_target = sorted(df_target['driver'].dropna().unique())
    rounds_target = sorted(df_target['round'].dropna().unique())

    if len(drivers_target) == 0 or len(rounds_target) == 0:
        return []

    hist = df[(df['season'] < end_year) & (df['driver'].isin(drivers_target))].copy()
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
        } for d in drivers_target])

    if perf.empty:
        perf = pd.DataFrame([{'driver': d, 'circuit_id': None, 'race_count': 0,
                              'avg_finish': np.nan, 'avg_grid': np.nan,
                              'podium_rate': np.nan, 'win_rate': np.nan, 'pts_per_race': np.nan}
                             for d in drivers_target])
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

    perf_lookup = perf.set_index(['driver', 'circuit_id']) if not perf.empty else None
    career_lookup = career_tmp.set_index('driver') if not career_tmp.empty else pd.DataFrame()

    UNKNOWN_DRIVER_START_RATING = 55.0
    out_records = []

    # --- Process each season and round ---
    for season in range(start_year, end_year + 1):
        df_season = df_target[df_target['season'] == season]
        rounds_season = sorted(df_season['round'].dropna().unique())

        for rnd in rounds_season:
            df_round = df_season[df_season['round'] == rnd]
            drivers_this_round = sorted(df_round['driver'].dropna().unique())
            circuit_ids = df_round['circuit_id'].dropna().unique()
            circuit_id = str(circuit_ids[0]) if len(circuit_ids) > 0 else None

            for driver in drivers_this_round:
                # --- Lookup track/career performance ---
                track_row = None
                if perf_lookup is not None and circuit_id is not None:
                    try:
                        row = perf_lookup.loc[(driver, circuit_id)]
                        if isinstance(row, pd.DataFrame):
                            row = row.iloc[0]
                        track_row = row
                    except KeyError:
                        track_row = None

                if track_row is not None:
                    rating = float(track_row['rating'])
                    race_count = int(track_row['race_count'])
                    career_score = float(track_row['career_score'])
                    combined_score = float(track_row['combined_score'])
                    track_raw_score = float(track_row['track_raw_score'])
                else:
                    if driver in career_lookup.index:
                        crow = career_lookup.loc[driver]
                        career_score = float(crow['career_score'])
                        combined_score = career_score
                        rating = round(50.0 + 50.0 * min(max(career_score, 0.0), 1.0), 1)
                        race_count = int(crow['career_race_count'])
                        track_raw_score = None
                    else:
                        career_score = float(cs_mean)
                        combined_score = career_score
                        rating = float(UNKNOWN_DRIVER_START_RATING)
                        race_count = 0
                        track_raw_score = None

                constructor = None
                driver_row = df_round[df_round['driver'] == driver]
                if not driver_row.empty:
                    row = driver_row.iloc[0]
                    for col in constructor_cols:
                        if int(row[col]) == 1:
                            constructor = col.replace("constructor_", "").replace("_f1", "").replace("_racing", "").capitalize()
                            break
                if constructor is None:
                    constructor = "Unknown"

                out_records.append({
                    "season": int(season),
                    "round": int(rnd),
                    "driver": str(driver),
                    "constructor": constructor,
                    "rating": float(round(float(rating), 1)),
                    "race_count": int(race_count),
                    "career_score": float(career_score),
                    "combined_score": float(combined_score),
                    "track_raw_score": float(track_raw_score) if track_raw_score is not None else None
                })

    # --- Structure final JSON ---
    season_records = []
    for season in range(start_year, end_year + 1):
        df_season = [r for r in out_records if r['season'] == season]
        if not df_season:
            continue
        rounds_season = sorted({r['round'] for r in df_season})
        season_data = {"season": season, "rounds": []}

        for rnd in rounds_season:
            predictions = []
            for r in df_season:
                if r['round'] == rnd:
                    predictions.append({
                        "driver": r['driver'],
                        "constructor": r['constructor'],
                        "rating": r['rating'],
                        "race_count": r['race_count'],
                        "career_score": r['career_score'],
                        "combined_score": r['combined_score'],
                        "track_raw_score": r['track_raw_score']
                    })
            season_data["rounds"].append({"round": rnd, "predictions": predictions})

        season_records.append(season_data)

    with open(RESULTS_PATH_DRIVERS, 'w') as f:
        json.dump(season_records, f, indent=2)

    print(f"Driver strengths saved to {RESULTS_PATH_DRIVERS} (seasons: {len(season_records)})")
    return season_records