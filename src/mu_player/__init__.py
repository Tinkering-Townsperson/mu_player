__version__ = "1.0.0"

import os
import webbrowser
from threading import Thread

import pystray
from PIL import Image
from flask import Flask, redirect, send_from_directory

from .config import COVERS_DIRECTORY, load_app_config

_browser_opened = False


def _tray_icon_thread(app):
	menu = pystray.Menu(
		pystray.MenuItem(
			'Open in browser',
			lambda:_open_browser_thread("http://localhost:5000"),
			default=True
		),
		pystray.MenuItem('Quit', on_quit)
	)
	icon = pystray.Icon(
		'μPlayer',
		icon=Image.open(os.path.join(app.root_path, "static/logo.png")),
		menu=menu,
	)
	icon.run()

def _open_browser_thread(url):
	"""Open browser in a background thread after a short delay."""
	import time
	time.sleep(1.5)  # Wait for server to be ready
	webbrowser.open(url)

def on_quit(icon, item):
	icon.stop()
	import os
	os._exit(0)

def create_app(test_config=None):
	global _browser_opened
	app = Flask(__name__, instance_relative_config=True)

	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		app.config.from_mapping(test_config)

	os.makedirs(app.instance_path, exist_ok=True)

	app_config = load_app_config()
	should_open_browser = app_config.get("open_browser_on_start", True)
	reloader_process = os.environ.get("WERKZEUG_RUN_MAIN")
	should_open_in_this_process = reloader_process == "true" or (reloader_process is None and not app.debug)
	if should_open_browser and should_open_in_this_process and not _browser_opened:
		_browser_opened = True
		url = "http://localhost:5000"
		browser_thread = Thread(target=_open_browser_thread, args=(url,), daemon=True)
		browser_thread.start()

	tray_thread = Thread(target=_tray_icon_thread, args=(app,), daemon=True)
	tray_thread.start()

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
