from flask import Blueprint, render_template
from metadata.track_metadata import TRACK_METADATA

tracks_bp = Blueprint("tracks", __name__, url_prefix="/tracks")

# Render individual track pages if they exist
@tracks_bp.route("/<trackname>")
def tracks(trackname):
    tracklist = []
    for key, track in TRACK_METADATA.items():
        tracklist.append({"id": key, **track})

    track = TRACK_METADATA.get(trackname)
    if not track:
        return render_template("homepage.html")

    return render_template(
        "track_template.html",
        tracks = tracklist,
        track_display_name=track["display_name"],
        f1_website=track["f1_website"],
        flag_path=f"/static/images/flags/{track['flag']}",
        annotated_layout_path=f"/static/images/annotated-layouts/annotated-{track['annotated_layout']}",
        round_number=track["round"],
        track_image=track["detailed_track_image"],
        track_attribution=track["detailed_track_attribution"],
        wiki=track["wiki"],
    )