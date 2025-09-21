import os
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for
from metadata.track_metadata import TRACK_METADATA
from typing import Any

tracks_bp = Blueprint("tracks", __name__, url_prefix="/tracks")

CURRENT_SEASON = 2025
MIN_SEASON = 2010
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FINAL_DF_PATH = os.path.join(BASE_DIR, "ml", "final_df.csv")
SEASON_COMPLETE = -1

try:
    _FINAL_DF = pd.read_csv(FINAL_DF_PATH)
except Exception as e:
    _FINAL_DF = pd.DataFrame()

def available_seasons():
    if _FINAL_DF.empty:
        return []
    seasons = sorted(_FINAL_DF['season'].dropna().astype(int).unique().tolist())
    return [s for s in seasons if s >= MIN_SEASON]

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

def get_placeholder_current_season_tracks():
    tracklist = []
    for key, meta in TRACK_METADATA.items():
        t = build_track_from_key(key, meta.get('round'))
        tracklist.append(t)
    tracklist.sort(key=lambda x: (x.get('round') if x.get('round') is not None else 999))
    return tracklist

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
            circuit_col_name = None
            for col in row.index:
                if not col.startswith("circuit_id_"):
                    continue

                value: Any = row.get(col)
                if pd.isna(value):
                    continue

                try:
                    if int(value) == 1:
                        circuit_col_name = col[len("circuit_id_"):]
                        break
                except (TypeError, ValueError):
                    continue

            placeholder_id = circuit_col_name.replace('_', '-') if circuit_col_name else f"round-{round_num}"
            placeholder_display_name = circuit_col_name.replace('_', ' ').title() if circuit_col_name else f"Round {round_num}"

            placeholder = {
                "id": placeholder_id,
                "display_name": placeholder_display_name,
                "f1_website": "2024/united-arab-emirates",
                "flag": "Flag_of_Placeholder.png",
                "detailed_flag": "Placeholder.png",
                "annotated_layout": "placeholder.avif",
                "layout": "placeholder.png",
                "detailed_track_image": "placeholder_detailed_track.jpg",
                "detailed_track_attribution": "",
                "round": round_num,
                "wiki": "",
                "date": "1st January",
            }
            tracks.append(placeholder)

    return tracks

# Render individual track pages if they exist
@tracks_bp.route("/<int:season>/<int:roundnum>/<trackname>")
def tracks(season, roundnum, trackname):
    if season < MIN_SEASON:
        return redirect(url_for("home.homepage_root"))

    seasons = available_seasons()

    # Build the tracklist exactly like homepage_year
    if season in seasons and season < CURRENT_SEASON:
        tracks = get_tracks_from_df_for_season(season)
    else:
        tracks = get_placeholder_current_season_tracks()

    track = TRACK_METADATA.get(trackname)
    if not track:
        return render_template("homepage.html")

    return render_template(
        "track_template.html",
        tracks=tracks,
        track_display_name=track["display_name"],
        f1_website=track["f1_website"],
        flag_path=f"/static/images/flags/{track['flag']}",
        annotated_layout_path=f"/static/images/annotated-layouts/annotated-{track['annotated_layout']}",
        round_number=roundnum,
        season_year=season,
        seasons=seasons,
        track_image=track["detailed_track_image"],
        track_attribution=track["detailed_track_attribution"],
        wiki=track["wiki"],
    )