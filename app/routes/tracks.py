from flask import Blueprint, render_template, redirect, url_for
from metadata.track_metadata import TRACK_METADATA

tracks_bp = Blueprint("tracks", __name__, url_prefix="/tracks")

MIN_SEASON = 2010
CURRENT_SEASON = 2025

# Render individual track pages if they exist
@tracks_bp.route("/<int:season>/<int:roundnum>/<trackname>")
def tracks(season, roundnum, trackname):
    if season < MIN_SEASON:
        return redirect(url_for("home.homepage_root"))

    tracklist = [{"id": key, **track} for key, track in TRACK_METADATA.items()]

    track = TRACK_METADATA.get(trackname)
    if not track:
        return render_template("homepage.html")

    return render_template(
        "track_template.html",
        tracks=tracklist,
        track_display_name=track["display_name"],
        f1_website=track["f1_website"],
        flag_path=f"/static/images/flags/{track['flag']}",
        annotated_layout_path=f"/static/images/annotated-layouts/annotated-{track['annotated_layout']}",
        round_number=roundnum,
        season_year=season,
        track_image=track["detailed_track_image"],
        track_attribution=track["detailed_track_attribution"],
        wiki=track["wiki"],
    )