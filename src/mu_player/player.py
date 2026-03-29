import random
from threading import Lock

from flask import (  # noqa
	Blueprint, g, render_template, request, url_for, jsonify
)
import time

from pathlib import Path

from .song import Song, pygame
bp = Blueprint("player", __name__, url_prefix="/player")

song_dir = Path(r"C:\Users\after\OneDrive\Music\good kid")

songs = list(Song(p) for p in song_dir.rglob("*.mp3"))
queue = songs.copy()
current_song_index = -1

current_song = None
playback_started_at = None
playback_paused_elapsed = None
repeat_mode = "none"  # none, one, all
auto_advance_lock = Lock()


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


def maybe_advance_finished_song():
	"""Advance to the next song when the current one ends naturally."""
	if not auto_advance_lock.acquire(blocking=False):
		return

	try:
		if current_song is None or playback_started_at is None:
			return

		if current_song.paused or not current_song.playing:
			return

		duration = current_song.duration
		if duration <= 0:
			return

		elapsed = time.monotonic() - playback_started_at
		# Advance if the mixer is idle (natural end) or elapsed reached duration.
		if not pygame.mixer.get_busy() or elapsed >= duration:
			current_song.stop()
			get_next_song()
	finally:
		auto_advance_lock.release()


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
		"shuffled": shuffled(),
		"repeat_mode": repeat_mode,
	}


def get_next_song():
	global current_song, current_song_index, playback_started_at, playback_paused_elapsed
	if repeat_mode == "one" and current_song is not None:
		# Repeat current song
		current_song.stop()
		current_song.play()
		playback_started_at = time.monotonic()
		playback_paused_elapsed = None
		return

	current_song_index += 1
	if current_song_index < len(queue):
		current_song = queue[current_song_index]
	else:
		if repeat_mode == "all" and len(queue) > 0:
			# Loop back to first song
			current_song_index = 0
			current_song = queue[0]
		else:
			current_song = None
			current_song_index = len(queue) - 1
	pygame.mixer.stop()
	print(f"Now playing: {current_song.stem if current_song else 'No more songs'}")
	if current_song:
		current_song.stop()
		current_song.play()
		playback_started_at = time.monotonic()
		playback_paused_elapsed = None
	else:
		playback_started_at = None
		playback_paused_elapsed = None


def get_previous_song():
	global current_song, current_song_index, playback_started_at, playback_paused_elapsed
	current_song_index = max(-1, current_song_index - 1)
	if current_song_index >= 0:
		current_song = queue[current_song_index]
	else:
		current_song = None
	pygame.mixer.stop()
	print(f"Now playing: {current_song.stem if current_song else 'No more songs'}")
	if current_song:
		current_song.stop()
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


def toggle_shuffle_queue():
	global queue, current_song_index

	if queue == songs:
		queue = songs.copy()
		if current_song in queue:
			queue.remove(current_song)
			queue.insert(0, current_song)

		random.shuffle(queue)
	else:
		queue = songs.copy()
		if current_song in queue:
			current_song_index = queue.index(current_song)
		else:
			current_song_index = -1


def toggle_repeat_mode():
	global repeat_mode
	if repeat_mode == "none":
		repeat_mode = "one"
	elif repeat_mode == "one":
		repeat_mode = "all"
	else:
		repeat_mode = "none"


@bp.route("/")
def index():
	if current_song is None:
		get_next_song()
	return render_template("player.html", current_song=current_song)


@bp.route("/state")
def state():
	maybe_advance_finished_song()
	return jsonify({"song": serialize_song(current_song), "shuffled": shuffled(), "repeat_mode": repeat_mode})


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


@bp.route("/previous", methods=["POST"])
def previous_song():
	get_previous_song()
	if current_song:
		return jsonify(serialize_song(current_song))
	return {"error": "No more songs"}, 204


@bp.route("/shuffle", methods=["POST"])
def toggle_shuffle():
	toggle_shuffle_queue()
	if current_song:
		return jsonify(serialize_song(current_song))
	return {"error": "No song loaded"}, 404


@bp.route("/repeat", methods=["POST"])
def toggle_repeat():
	toggle_repeat_mode()
	if current_song:
		return jsonify(serialize_song(current_song))
	return {"error": "No song loaded"}, 404


def shuffled():
	return queue != songs
