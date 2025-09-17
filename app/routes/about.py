from flask import Blueprint, render_template
from metadata.track_metadata import TRACK_METADATA

about_bp = Blueprint("about", __name__, template_folder="../templates")

@about_bp.route("/")
def about():
    return render_template("about.html")
