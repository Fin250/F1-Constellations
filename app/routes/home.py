import os
import json
import pandas as pd
from flask import Blueprint, redirect, render_template, url_for

from metadata.track_metadata import TRACK_METADATA

CURRENT_SEASON = 2024
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FINAL_DF_PATH = os.path.join(BASE_DIR, "..", "ml", "final_df.csv")
SEASON_COMPLETE = -1

try:
    _FINAL_DF = pd.read_csv(FINAL_DF_PATH)
except Exception:
    _FINAL_DF = pd.DataFrame()

home_bp = Blueprint("home", __name__)

def available_seasons():
    if _FINAL_DF.empty:
        return []
    return sorted(_FINAL_DF['season'].dropna().astype(int).unique().tolist())

def circuit_key_from_row(row):
    if row is None or row.empty:
        return None
    for col in row.index:
        if col.startswith('circuit_id_') and pd.notna(row[col]) and int(row[col]) == 1:
            return col.replace('circuit_id_', '')
    return None

def build_track_from_key(key, round_num=None):
    meta = TRACK_METADATA.get(key, {})
    return {
        "id": key,
        "display_name": meta.get("display_name", key.replace('_', ' ').title()),
        "layout": meta.get("layout", ""),
        "flag": meta.get("flag", ""),
        "detailed_flag": meta.get("detailed_flag", ""),
        "annotated_layout": meta.get("annotated_layout", ""),
        "detailed_track_image": meta.get("detailed_track_image", ""),
        "detailed_track_attribution": meta.get("detailed_track_attribution", ""),
        "round": int(round_num) if round_num is not None else meta.get("round"),
        "wiki": meta.get("wiki", ""),
        "date": meta.get("date", "")
    }

# build tracklist for a past season from final_df
def get_tracks_from_df_for_season(year: int):
    if _FINAL_DF.empty:
        return []

    df_year = _FINAL_DF[_FINAL_DF['season'] == int(year)]
    if df_year.empty:
        return []

    if 'round' in df_year.columns:
        df_year = df_year.sort_values('round').drop_duplicates(subset=['round'])
    else:
        df_year = df_year.reset_index(drop=True)

    tracks = []

    for _, row in df_year.iterrows():
        try:
            round_num = int(row['round'])
        except (TypeError, ValueError):
            continue

        key = None
        for track_key, meta in TRACK_METADATA.items():
            circuit_col = meta.get("circuit_id")
            if isinstance(circuit_col, str) and circuit_col in row.index:
                val = row[circuit_col]
                if pd.notna(val) and int(val) == 1:
                    key = track_key
                    break

        if key:
            t = build_track_from_key(key, round_num)
            tracks.append(t)
        else:
            found = None
            for k, v in TRACK_METADATA.items():
                if v.get('round') == round_num:
                    found = build_track_from_key(k, round_num)
                    break
            if found:
                tracks.append(found)
            else:
                tracks.append({
                    "id": f"round-{round_num}",
                    "display_name": f"Round {round_num}",
                    "layout": "",
                    "flag": "",
                    "detailed_flag": "",
                    "round": round_num,
                    "wiki": "",
                    "date": ""
                })
    for t in tracks:
        if t["round"] is None:
            print("Track with None round:", t)

    print(tracks)
    return tracks

def get_placeholder_current_season_tracks():
    tracklist = []
    for key, meta in TRACK_METADATA.items():
        t = build_track_from_key(key, meta.get('round'))
        tracklist.append(t)
    tracklist.sort(key=lambda x: (x.get('round') if x.get('round') is not None else 999))
    return tracklist

def get_next_track():
    return 16  # hardcoded next round

# Homepage route
@home_bp.route("/")
def homepage_root():
    return redirect(url_for('home.homepage_year', year=CURRENT_SEASON))

@home_bp.route("/<int:year>")
def homepage_year(year):
    year = int(year)
    seasons = available_seasons()

    if year in seasons and year < CURRENT_SEASON:
        tracks = get_tracks_from_df_for_season(year)
        next_round = SEASON_COMPLETE
    else:
        tracks = get_placeholder_current_season_tracks()
        next_round = get_next_track() if year == CURRENT_SEASON else None

    return render_template(
        "homepage.html",
        tracks=tracks,
        next_round=next_round,
        year=year,
        seasons=seasons
    )