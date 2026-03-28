from flask import (  # noqa
	Blueprint, g, render_template, request, url_for, jsonify
)
import time

from pathlib import Path

from .song import Song, pygame
bp = Blueprint("player", __name__, url_prefix="/player")

song_dir = Path(r"C:\Users\after\OneDrive\Music\good kid")

songs = (Song(p) for p in song_dir.rglob("*.mp3"))

current_song = None
playback_started_at = None
playback_paused_elapsed = None


def get_song_elapsed_seconds(song):
	if song is None or playback_started_at is None:
		return 0.0

	if playback_paused_elapsed is not None:
		return playback_paused_elapsed

	duration = song.duration
	if duration <= 0:
		return 0.0

	elapsed = time.monotonic() - playback_started_at
	if elapsed < 0:
		return 0.0

	return min(elapsed, duration)


def serialize_song(song: Song):
	if song is None:
		return None

	cover_url = url_for("covers", filename=song.coverfile) if song.cover else url_for("static", filename="default_cover.png")
	elapsed = get_song_elapsed_seconds(song)
	return {
		"title": song.title,
		"tracknum": song.tracknum,
		"artist": song.artist,
		"album": song.album,
		"cover": cover_url,
		"key": song.stem,
		"duration": song.duration,
		"elapsed": elapsed,
		"is_paused": song.paused,
		"is_playing": song.playing and not song.paused,
	}


def get_next_song():
	global current_song, playback_started_at, playback_paused_elapsed
	current_song = next(songs, None)
	pygame.mixer.stop()
	print(f"Now playing: {current_song.stem if current_song else 'No more songs'}")
	if current_song:
		current_song.play()
		playback_started_at = time.monotonic()
		playback_paused_elapsed = None
	else:
		playback_started_at = None
		playback_paused_elapsed = None


def toggle_song_playback():
	global playback_started_at, playback_paused_elapsed

	if current_song is None:
		return

	if current_song.paused:
		current_song.play()
		if playback_paused_elapsed is not None:
			playback_started_at = time.monotonic() - playback_paused_elapsed
		playback_paused_elapsed = None
	else:
		playback_paused_elapsed = get_song_elapsed_seconds(current_song)
		current_song.pause()


@bp.route("/")
def index():
	if current_song is None:
		get_next_song()
	return render_template("player.html", current_song=current_song)


@bp.route("/state")
def state():
	return jsonify({"song": serialize_song(current_song)})


@bp.route("/next", methods=["POST"])
def next_song():
	get_next_song()
	if current_song:
		return jsonify(serialize_song(current_song))
	return {"error": "No more songs"}, 204


@bp.route("/toggle-playback", methods=["POST"])
def toggle_playback():
	toggle_song_playback()
	if current_song:
		return jsonify(serialize_song(current_song))
	return {"error": "No song loaded"}, 404
