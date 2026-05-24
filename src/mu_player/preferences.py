from flask import (  # noqa
	Blueprint, render_template, request
)

from .config import load_app_config, save_app_config

bp = Blueprint("preferences", __name__, url_prefix="/preferences")


@bp.route("/", methods=["GET", "POST"])
def index():
	message = None
	error = None
	config = load_app_config()

	if request.method == "POST":
		music_folder_changed = False
		current_music_folder = config.get("music_folder", "")
		music_folder = request.form.get("music_folder", "").strip()
		if not music_folder:
			error = "Music folder is required."
		else:
			music_folder_changed = music_folder != current_music_folder
			config["music_folder"] = music_folder
			config["show_cover_art"] = request.form.get("show_cover_art") == "on"
			config["auto_play_on_open"] = request.form.get("auto_play_on_open") == "on"
			config["open_browser_on_start"] = request.form.get("open_browser_on_start") == "on"

			default_volume = request.form.get("default_volume", "").strip()
			try:
				default_volume_value = int(default_volume)
			except ValueError:
				error = "Default volume must be a number between 0 and 100."
			else:
				if default_volume_value < 0 or default_volume_value > 100:
					error = "Default volume must be between 0 and 100."
				else:
					config["default_volume"] = default_volume_value

		if error is None:
			config = save_app_config(config)
			from . import player
			player.reload_runtime_preferences(reload_library=music_folder_changed)
			message = "Preferences saved and applied."

	return render_template(
		"preferences.html",
		config=config,
		message=message,
		error=error,
	)
