from flask import (  # noqa
	Blueprint, g, render_template, request, url_for
)

bp = Blueprint("preferences", __name__, url_prefix="/preferences")


@bp.route("/")
def index():
	return render_template("preferences.html")
