__version__ = "1.0.0"

import os

from flask import Flask, send_from_directory

from .config import COVERS_DIRECTORY


def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)

	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		app.config.from_mapping(test_config)

	os.makedirs(app.instance_path, exist_ok=True)

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
