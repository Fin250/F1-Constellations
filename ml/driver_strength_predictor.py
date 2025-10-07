import json
import os
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_PATH_DRIVERS = os.path.join(BASE_DIR, "driver_strengths.json")
FINAL_DF_PATH = os.path.join(BASE_DIR, "final_df.csv")

def predict_driver_strengths(start_year: int = 2010, end_year: int = 2025):
    print(f"Calculating driver strengths from {start_year} to {end_year}...")
    df = pd.read_csv(FINAL_DF_PATH)
    if df.empty:
        return []

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

    # helpers
    def wavg(vals, weights):
        vals = np.array(vals, dtype=float)
        weights = np.array(weights, dtype=float)
        mask = ~np.isnan(vals)
        if mask.sum() == 0 or weights[mask].sum() == 0:
            return np.nan
        return (vals[mask] * weights[mask]).sum() / weights[mask].sum()

    def minmax(series, fillna_val=0.5):
        s = pd.Series(series).astype(float)
        if s.isnull().all():
            return pd.Series(fillna_val, index=s.index)
        s = s.fillna(s.median())
        mn, mx = s.min(), s.max()
        if np.isclose(mx, mn):
            return pd.Series(0.5, index=s.index)
        return (s - mn) / (mx - mn)

    UNKNOWN_DRIVER_START_RATING = 55.0
    PRIOR_COUNT = 5.0

    # F1 points mapping for derived points_count
    points_map = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }

    out_records = []

    # --- Process each season and round; build history up-to-and-including that season ---
    for season in range(start_year, end_year + 1):
        hist = df[(df['season'] <= season) & df['driver'].notna()].copy()

        # Ensure columns exist
        for col in ['podium', 'grid', 'driver_points']:
            if col not in hist.columns:
                hist[col] = np.nan

        hist['podium'] = pd.to_numeric(hist['podium'], errors='coerce')
        hist['grid'] = pd.to_numeric(hist['grid'], errors='coerce')

        hist['derived_points'] = hist['podium'].map(points_map).fillna(0.0).astype(float)

        if 'driver_points' not in hist or hist['driver_points'].isnull().all():
            hist['driver_points'] = hist['derived_points']
        else:
            hist['driver_points'] = pd.to_numeric(hist['driver_points'], errors='coerce').fillna(hist['derived_points'])

        hist['podium_top3'] = (hist['podium'] <= 3).astype(float)
        hist['win_flag'] = (hist['podium'] == 1).astype(float)

        # season weighting relative to the current season being processed:
        SEASON_DECAY = 0.5
        if not hist.empty:
            ref_season = int(season)
            hist['season_weight'] = np.exp(-SEASON_DECAY * (ref_season - hist['season']))
        else:
            hist['season_weight'] = pd.Series(dtype=float)

        def extract_ctor_name(row):
            for col in constructor_cols:
                try:
                    if int(row.get(col, 0)) == 1:
                        return col.replace("constructor_", "").replace("_f1", "").replace("_racing", "").lower()
                except Exception:
                    continue
            return None

        if len(constructor_cols) > 0:
            hist['ctor_name'] = pd.Series([extract_ctor_name(row) for _, row in hist.iterrows()], index=hist.index, dtype=object)
        else:
            hist['ctor_name'] = pd.Series([None] * len(hist), index=hist.index, dtype=object)

        # per-track performance and objective aggregates
        track_records = []
        if not hist.empty:
            for (driver, circuit), sub in hist.groupby(['driver', 'circuit_id'], dropna=False):
                if pd.isna(driver) or pd.isna(circuit):
                    continue
                w = sub['season_weight'].fillna(1.0)

                race_count = int(len(sub))
                win_count = int(sub['win_flag'].sum())
                points_count = int(sub['derived_points'].sum())

                grid_num = pd.to_numeric(sub['grid'], errors='coerce')
                pod_num = pd.to_numeric(sub['podium'], errors='coerce')
                overtakes = (grid_num - pod_num).dropna().sum()
                overtakes_count = int(overtakes) if not np.isnan(overtakes) else 0

                track_records.append({
                    'driver': driver,
                    'circuit_id': str(circuit),
                    'race_count': race_count,
                    'win_count': win_count,
                    'points_count': points_count,
                    'overtakes_count': overtakes_count,
                    'avg_finish': wavg(sub['podium'], w),
                    'avg_grid': wavg(sub['grid'], w),
                    'podium_rate': wavg(sub['podium_top3'], w),
                    'win_rate': wavg(sub['win_flag'], w),
                    'pts_per_race': wavg(sub['derived_points'], w)
                })
        perf = pd.DataFrame(track_records)

        driver_records = []
        if not hist.empty:
            for driver, sub in hist.groupby('driver'):
                w = sub['season_weight'].fillna(1.0)
                driver_records.append({
                    'driver': driver,
                    'count_all': int(len(sub)),
                    'avg_finish_all': wavg(sub['podium'], w),
                    'avg_grid_all': wavg(sub['grid'], w),
                    'podium_rate_all': wavg(sub['podium_top3'], w),
                    'win_rate_all': wavg(sub['win_flag'], w),
                    'pts_per_race_all': wavg(sub['derived_points'], w)
                })
        driver_perf = pd.DataFrame(driver_records)
        if driver_perf.empty:
            driver_perf = pd.DataFrame([{
                'driver': d,
                'count_all': 0,
                'avg_finish_all': np.nan,
                'avg_grid_all': np.nan,
                'podium_rate_all': np.nan,
                'win_rate_all': np.nan,
                'pts_per_race_all': np.nan
            } for d in drivers_target])

        # --- compute overall driver track_raw_score ---
        df_tmp = driver_perf.copy()
        finish_score_all = 1.0 - minmax(df_tmp.get('avg_finish_all', pd.Series(dtype=float)))
        grid_score_all = 1.0 - minmax(df_tmp.get('avg_grid_all', pd.Series(dtype=float)))
        podium_score_all = minmax(df_tmp.get('podium_rate_all', pd.Series(dtype=float)))
        win_score_all = minmax(df_tmp.get('win_rate_all', pd.Series(dtype=float)))
        pts_score_all = minmax(df_tmp.get('pts_per_race_all', pd.Series(dtype=float)))
        df_tmp['track_raw_all'] = (
            0.35 * finish_score_all +
            0.30 * podium_score_all +
            0.15 * win_score_all +
            0.10 * pts_score_all +
            0.10 * grid_score_all
        )
        df_tmp['track_raw_all_pct'] = (df_tmp['track_raw_all'] * 100).fillna(0.0)
        overall_lookup = df_tmp.set_index('driver') if not df_tmp.empty else pd.DataFrame()

        # --- wet/dry subsets for weather-specific ratings ---
        hist['is_wet'] = (
            hist['weather_wet'].fillna(False).astype(bool)
            if 'weather_wet' in hist.columns
            else pd.Series(False, index=hist.index, dtype=bool)
        )

        def compute_weather_perf(subset):
            recs = []
            if not subset.empty:
                for driver, s2 in subset.groupby('driver'):
                    w = s2['season_weight'].fillna(1.0)
                    recs.append({
                        'driver': driver,
                        'avg_finish': wavg(s2['podium'], w),
                        'avg_grid': wavg(s2['grid'], w),
                        'podium_rate': wavg(s2['podium_top3'], w),
                        'win_rate': wavg(s2['win_flag'], w),
                        'pts_per_race': wavg(s2['derived_points'], w)
                    })
            return pd.DataFrame(recs)

        wet_perf = compute_weather_perf(hist[hist['is_wet']])
        dry_perf = compute_weather_perf(hist[~hist['is_wet']])

        def add_track_raw_to(df_weather):
            if df_weather.empty:
                return df_weather
            dfw = df_weather.copy()
            dfw['finish_score'] = 1.0 - minmax(dfw.get('avg_finish', pd.Series(dtype=float)))
            dfw['grid_score'] = 1.0 - minmax(dfw.get('avg_grid', pd.Series(dtype=float)))
            dfw['podium_score'] = minmax(dfw.get('podium_rate', pd.Series(dtype=float)))
            dfw['win_score'] = minmax(dfw.get('win_rate', pd.Series(dtype=float)))
            dfw['pts_score'] = minmax(dfw.get('pts_per_race', pd.Series(dtype=float)))
            dfw['track_raw'] = (
                0.35 * dfw['finish_score'] +
                0.30 * dfw['podium_score'] +
                0.15 * dfw['win_score'] +
                0.10 * dfw['pts_score'] +
                0.10 * dfw['grid_score']
            )
            dfw['track_raw_pct'] = (dfw['track_raw'] * 100).fillna(0.0)
            return dfw

        wet_perf = add_track_raw_to(wet_perf)
        dry_perf = add_track_raw_to(dry_perf)

        # --- per-circuit perf calculations (track_raw_score) ---
        perf = perf.merge(driver_perf[['driver', 'count_all', 'avg_finish_all']], on='driver', how='left')

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

        # --- build career_tmp (driver-level) and compute career_score & career_rating ---
        career_tmp = pd.DataFrame({'driver': drivers_target})
        career_tmp = career_tmp.merge(driver_perf, on='driver', how='left')

        # compute career_score (driver-level)
        c_finish = 1.0 - minmax(career_tmp.get('avg_finish_all', pd.Series(dtype=float)))
        c_grid = 1.0 - minmax(career_tmp.get('avg_grid_all', pd.Series(dtype=float)))
        c_podium = minmax(career_tmp.get('podium_rate_all', pd.Series(dtype=float)))
        c_win = minmax(career_tmp.get('win_rate_all', pd.Series(dtype=float)))
        c_pts = minmax(career_tmp.get('pts_per_race_all', pd.Series(dtype=float)))
        career_tmp['career_score'] = (
            0.35 * c_finish + 0.30 * c_podium + 0.15 * c_win + 0.10 * c_pts + 0.10 * c_grid
        )

        # fill missing career_score with mean
        cs_mean = career_tmp['career_score'].mean() if 'career_score' in career_tmp.columns else 0.5
        if np.isnan(cs_mean):
            cs_mean = 0.5
        career_tmp['career_score'] = career_tmp['career_score'].fillna(cs_mean)

        # career_race_count
        if 'count_all' in career_tmp.columns:
            career_tmp['career_race_count'] = career_tmp['count_all'].fillna(0).astype(int)
        else:
            career_tmp['career_race_count'] = pd.Series(0, index=career_tmp.index, dtype=int)

        # career_rating mapping
        career_tmp['career_score_clipped'] = career_tmp['career_score'].clip(0.0, 1.0)
        career_tmp['career_rating'] = (50.0 + 50.0 * career_tmp['career_score_clipped']).round(1)

        # merge career info into perf
        perf = perf.merge(career_tmp[['driver', 'career_score', 'career_race_count', 'career_rating']], on='driver', how='left')

        # combine track & career into combined_score & rating
        perf['n'] = perf['race_count'].fillna(0).astype(float)
        perf['k'] = float(PRIOR_COUNT)
        tr_mean = perf['track_raw_score'].mean() if 'track_raw_score' in perf else 0.5
        cs_mean_for_perf = perf['career_score'].mean() if 'career_score' in perf else 0.5
        if np.isnan(tr_mean):
            tr_mean = 0.5
        if np.isnan(cs_mean_for_perf):
            cs_mean_for_perf = 0.5

        perf['combined_score'] = (
            perf['n'] * perf['track_raw_score'].fillna(tr_mean) +
            perf['k'] * perf['career_score'].fillna(cs_mean_for_perf)
        ) / (perf['n'] + perf['k'])

        perf['combined_score'] = perf['combined_score'].fillna(perf['combined_score'].mean() if not perf['combined_score'].isnull().all() else 0.5)
        perf['combined_score_clipped'] = perf['combined_score'].clip(0.0, 1.0)
        perf['rating'] = (50.0 + 50.0 * perf['combined_score_clipped']).round(1)

        # compute track_rating per circuit-row
        perf['track_raw_score'] = perf['track_raw_score'].fillna(perf['track_raw_score'].mean() if not perf['track_raw_score'].isnull().all() else 0.5)
        perf['track_raw_score_clipped'] = perf['track_raw_score'].clip(0.0, 1.0)
        perf['track_rating'] = (50.0 + 50.0 * perf['track_raw_score_clipped']).round(1)

        # finalize lookups
        perf_lookup = perf.set_index(['driver', 'circuit_id']) if not perf.empty else None
        career_lookup = career_tmp.set_index('driver') if not career_tmp.empty else pd.DataFrame()

        # --- quali signals ---
        if 'ctor_name' in hist.columns:
            grouped = hist.groupby(['season', 'round', 'ctor_name'])
        else:
            grouped = None

        quali_recs = {d: {'teammate_vals': [], 'teammate_weights': [], 'gain_vals': [], 'gain_weights': []} for d in drivers_target}

        for _, row in hist.iterrows():
            d = row['driver']
            if pd.isna(d):
                continue
            w = row.get('season_weight', 1.0) if not pd.isna(row.get('season_weight', np.nan)) else 1.0
            grid = row.get('grid')
            podium = row.get('podium')

            try:
                if not pd.isna(grid) and not pd.isna(podium):
                    gain = float(grid) - float(podium)
                    if not np.isnan(gain):
                        quali_recs[d]['gain_vals'].append(max(0.0, gain))
                        quali_recs[d]['gain_weights'].append(w)

                if 'ctor_name' in hist.columns and row.get('ctor_name') is not None and grouped is not None:
                    key = (row['season'], row['round'], row['ctor_name'])
                    try:
                        grp = grouped.get_group(key)
                        mates = grp[grp['driver'] != d]
                        if not mates.empty:
                            mate_grid = pd.to_numeric(mates.iloc[0].get('grid', np.nan), errors='coerce')
                            if not pd.isna(mate_grid) and not pd.isna(grid):
                                teammate_adv = float(mate_grid) - float(grid)
                                quali_recs[d]['teammate_vals'].append(teammate_adv)
                                quali_recs[d]['teammate_weights'].append(w)
                    except KeyError:
                        pass
            except Exception:
                continue

        quali_rows = []
        for driver, rec in quali_recs.items():
            t_vals = np.array(rec['teammate_vals'], dtype=float) if rec['teammate_vals'] else np.array([], dtype=float)
            t_w = np.array(rec['teammate_weights'], dtype=float) if rec['teammate_weights'] else np.array([], dtype=float)
            g_vals = np.array(rec['gain_vals'], dtype=float) if rec['gain_vals'] else np.array([], dtype=float)
            g_w = np.array(rec['gain_weights'], dtype=float) if rec['gain_weights'] else np.array([], dtype=float)

            def wmean(vals, weights):
                if vals.size == 0:
                    return np.nan
                mask = ~np.isnan(vals)
                if mask.sum() == 0 or weights[mask].sum() == 0:
                    return np.nan
                return (vals[mask] * weights[mask]).sum() / weights[mask].sum()

            t_mean = wmean(t_vals, t_w)
            g_mean = wmean(g_vals, g_w)
            quali_rows.append({'driver': driver, 'teammate_adv': t_mean, 'qual_gain': g_mean})

        quali_df = pd.DataFrame(quali_rows)
        if quali_df.empty:
            quali_df = pd.DataFrame([{'driver': d, 'teammate_adv': np.nan, 'qual_gain': np.nan} for d in drivers_target])

        teammate_norm = minmax(quali_df.get('teammate_adv', pd.Series(dtype=float)))
        gain_norm = minmax(quali_df.get('qual_gain', pd.Series(dtype=float)))

        combined_raw = []
        for i, drv in enumerate(quali_df['driver'].tolist()):
            t = teammate_norm.iloc[i] if i < len(teammate_norm) else np.nan
            g = gain_norm.iloc[i] if i < len(gain_norm) else np.nan
            if np.isnan(t) and np.isnan(g):
                raw = np.nan
            elif np.isnan(t):
                raw = g
            elif np.isnan(g):
                raw = t
            else:
                raw = 0.6 * t + 0.4 * g
            combined_raw.append(raw)
        quali_df['quali_raw'] = combined_raw
        quali_df['quali_rating'] = quali_df['quali_raw'].apply(lambda x: int(round(1 + 98 * x)) if not pd.isna(x) else 55)
        quali_lookup = quali_df.set_index('driver') if not quali_df.empty else pd.DataFrame()

        wet_lookup = wet_perf.set_index('driver') if not wet_perf.empty else pd.DataFrame()
        dry_lookup = dry_perf.set_index('driver') if not dry_perf.empty else pd.DataFrame()

        # helper fallback functions for wet/dry
        def get_wet_pct(dr):
            if dr in wet_lookup.index and 'track_raw_pct' in wet_lookup.columns:
                val = wet_lookup.loc[dr]['track_raw_pct']
                if not pd.isna(val):
                    return float(val)
            if dr in overall_lookup.index and 'track_raw_all_pct' in overall_lookup.columns:
                return float(overall_lookup.loc[dr]['track_raw_all_pct'])
            return 0.0

        def get_dry_pct(dr):
            if dr in dry_lookup.index and 'track_raw_pct' in dry_lookup.columns:
                val = dry_lookup.loc[dr]['track_raw_pct']
                if not pd.isna(val):
                    return float(val)
            if dr in overall_lookup.index and 'track_raw_all_pct' in overall_lookup.columns:
                return float(overall_lookup.loc[dr]['track_raw_all_pct'])
            return 0.0

        df_season = df_target[df_target['season'] == season]
        rounds_season = sorted(df_season['round'].dropna().unique())

        for rnd in rounds_season:
            df_round = df_season[df_season['round'] == rnd]
            drivers_this_round = sorted(df_round['driver'].dropna().unique())
            circuit_ids = df_round['circuit_id'].dropna().unique()
            circuit_id = str(circuit_ids[0]) if len(circuit_ids) > 0 else None

            for driver in drivers_this_round:
                # lookup circuit-row if available
                track_row = None
                if perf_lookup is not None and circuit_id is not None:
                    try:
                        row = perf_lookup.loc[(driver, circuit_id)]
                        if isinstance(row, pd.DataFrame):
                            row = row.iloc[0]
                        track_row = row
                    except KeyError:
                        track_row = None

                if isinstance(track_row, pd.Series):
                    rating = float(track_row.get('rating', UNKNOWN_DRIVER_START_RATING))
                    track_rating = float(track_row.get('track_rating', UNKNOWN_DRIVER_START_RATING))
                    career_rating = float(track_row.get('career_rating', UNKNOWN_DRIVER_START_RATING))
                    race_count = int(track_row.get('race_count', 0))
                    career_score = float(track_row.get('career_score', cs_mean if 'cs_mean' in locals() else 0.5))
                    combined_score = float(track_row.get('combined_score', career_score))
                    track_raw_score = (float(track_row['track_raw_score']) if 'track_raw_score' in track_row and pd.notna(track_row['track_raw_score']) else None)
                    win_count = int(track_row.get('win_count', 0))
                    points_count = int(track_row.get('points_count', 0))
                    overtakes_count = int(track_row.get('overtakes_count', 0))
                    val = track_row.get('avg_finish', None)
                    average_finish = None if val is None or pd.isna(val) else float(val)
                else:
                    # fall back to career_lookup
                    if driver in career_lookup.index:
                        crow = career_lookup.loc[driver]
                        career_score = float(crow['career_score'])
                        career_rating = float(crow.get('career_rating', UNKNOWN_DRIVER_START_RATING))
                        combined_score = career_score
                        rating = round(50.0 + 50.0 * min(max(career_score, 0.0), 1.0), 1)
                        race_count = int(crow.get('career_race_count', 0)) if 'career_race_count' in crow else int(crow.get('count_all', 0))
                        track_raw_score = None
                        track_rating = float(UNKNOWN_DRIVER_START_RATING)
                        win_count = 0
                        points_count = 0
                        overtakes_count = 0
                        average_finish = None
                    else:
                        career_score = 0.5
                        career_rating = UNKNOWN_DRIVER_START_RATING
                        combined_score = career_score
                        rating = float(UNKNOWN_DRIVER_START_RATING)
                        race_count = 0
                        track_raw_score = None
                        track_rating = float(UNKNOWN_DRIVER_START_RATING)
                        win_count = 0
                        points_count = 0
                        overtakes_count = 0
                        average_finish = None

                constructor = "Unknown"
                driver_row = df_round[df_round['driver'] == driver]
                if not driver_row.empty:
                    row = driver_row.iloc[0]
                    for col in constructor_cols:
                        try:
                            if int(row.get(col, 0)) == 1:
                                constructor = col.replace("constructor_", "").replace("_f1", "").replace("_racing", "").capitalize()
                                break
                        except Exception:
                            continue

                # weather & quali lookups
                dry_rating = get_dry_pct(driver)
                wet_rating = get_wet_pct(driver)
                quali_rating = int(quali_lookup.loc[driver]['quali_rating']) if (driver in quali_lookup.index and 'quali_rating' in quali_lookup.columns) else 55

                out_records.append({
                    "season": int(season),
                    "round": int(rnd),
                    "driver": str(driver),
                    "constructor": constructor,
                    "rating": float(round(float(rating), 1)),
                    "career_rating": float(round(float(career_rating), 1)),
                    "track_rating": float(round(float(track_rating), 1)),
                    "race_count": int(race_count),
                    "career_score": float(career_score),
                    "combined_score": float(combined_score),
                    "track_raw_score": float(track_raw_score) if track_raw_score is not None else None,
                    "win_count": int(win_count),
                    "points_count": int(points_count),
                    "overtakes_count": int(overtakes_count),
                    "average_finish": float(round(average_finish, 2)) if average_finish is not None and not pd.isna(average_finish) else None,
                    "dry_rating": float(round(dry_rating, 1)),
                    "wet_rating": float(round(wet_rating, 1)),
                    "quali_rating": int(quali_rating)
                })

    season_records = []
    for season in range(start_year, end_year + 1):
        df_season_records = [r for r in out_records if r['season'] == season]
        if not df_season_records:
            continue
        rounds_season = sorted({r['round'] for r in df_season_records})
        season_data = {"season": season, "rounds": []}

        for rnd in rounds_season:
            predictions = []
            for r in df_season_records:
                if r['round'] == rnd:
                    predictions.append({
                        "driver": r['driver'],
                        "constructor": r['constructor'],
                        "rating": r['rating'],
                        "career_rating": r.get('career_rating', 55),
                        "track_rating": r.get('track_rating', 55),
                        "race_count": r['race_count'],
                        "career_score": r['career_score'],
                        "combined_score": r['combined_score'],
                        "track_raw_score": r['track_raw_score'],
                        "win_count": r.get('win_count', 0),
                        "points_count": r.get('points_count', 0),
                        "overtakes_count": r.get('overtakes_count', 0),
                        "average_finish": r.get('average_finish'),
                        "dry_rating": r.get('dry_rating', 0.0),
                        "wet_rating": r.get('wet_rating', 0.0),
                        "quali_rating": r.get('quali_rating', 55),
                        "dnf_rate": 99,
                    })
            season_data["rounds"].append({"round": rnd, "predictions": predictions})

        season_records.append(season_data)

    with open(RESULTS_PATH_DRIVERS, 'w') as f:
        json.dump(season_records, f, indent=2)

    print(f"Driver strengths saved to {RESULTS_PATH_DRIVERS} (seasons: {len(season_records)})")
    return season_records