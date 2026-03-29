__version__ = "1.0.0"

import os
import webbrowser
from threading import Thread

from flask import Flask, redirect, send_from_directory

from .config import COVERS_DIRECTORY

_browser_opened = False


def _open_browser_thread(url):
	"""Open browser in a background thread after a short delay."""
	import time
	time.sleep(1.5)  # Wait for server to be ready
	webbrowser.open(url)


def create_app(test_config=None):
	global _browser_opened
	app = Flask(__name__, instance_relative_config=True)

	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		app.config.from_mapping(test_config)

	os.makedirs(app.instance_path, exist_ok=True)

	# Open browser once on first request
	@app.before_request
	def open_browser_once():
		global _browser_opened
		if not _browser_opened:
			_browser_opened = True
			url = "http://localhost:5000"
			thread = Thread(target=_open_browser_thread, args=(url,), daemon=True)
			thread.start()

	@app.route("/")
	def index():
		return redirect("/player")

	@app.route("/hello")
	def hello():
		return "Hello, world!"

	@app.route("/favicon.ico")
	def favicon():
		return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico", mimetype="image/x-icon")

	@app.route("/covers/<path:filename>")
	def covers(filename):
		return send_from_directory(COVERS_DIRECTORY, filename)

	from . import player
	app.register_blueprint(player.bp)

	from . import preferences
	app.register_blueprint(preferences.bp)

	from . import connect
	app.register_blueprint(connect.bp)

	return app
