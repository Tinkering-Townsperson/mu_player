import eyed3
from pathlib import Path
from datetime import timedelta
import srt
from .config import COVERS_DIRECTORY
import pygame

pygame.mixer.init()


def parse_embedded_srt(text: str) -> list[dict]:
	if not text or not text.strip():
		return []

	try:
		subtitles = list(srt.parse(text))
	except (srt.SRTParseError, ValueError, TypeError):
		return []

	cues = []

	for index, subtitle in enumerate(subtitles):
		text = subtitle.content.strip()

		if not text:
			continue

		start_ms = max(0, round(subtitle.start.total_seconds() * 1000))
		end_ms = max(0, round(subtitle.end.total_seconds() * 1000))

		if end_ms <= start_ms:
			continue

		cues.append({
			"index": subtitle.index or index + 1,
			"start_ms": start_ms,
			"end_ms": end_ms,
			"text": text,
		})

	return sorted(cues, key=lambda cue: cue["start_ms"])


class Song:
	@staticmethod
	def sanitize_filename_component(value: str) -> str:
		# Remove characters that are illegal in Windows filenames.
		illegal_chars = '<>:"/\\|?*'
		translation_table = str.maketrans("", "", illegal_chars)
		sanitized = value.translate(translation_table)

		# Drop ASCII control characters and trim trailing dots/spaces.
		sanitized = "".join(ch for ch in sanitized if ord(ch) >= 32).rstrip(" .")
		return sanitized or "Unknown"

	def __init__(self, path: Path):
		self.path = Path(path)
		self.metadatafile = eyed3.load(self.path)
		self.audio = None
		self.duration = 0.0

		if self.metadatafile is None:
			raise ValueError(f"Could not load audio file: {self.path}")

		if self.metadatafile.info and self.metadatafile.info.time_secs:
			self.duration = float(self.metadatafile.info.time_secs)

		self.playing = False
		self.paused = False

		self.title = self.path.stem
		self.artist = "Unknown Artist"
		self.album = "Unknown Album"
		self.tracknum = None

		self.lyrics = None
		self.lyrics_format = "plain"
		self.lyrics_cues = []

		self.cover = None
		self.coverfile = None

		if self.metadatafile.tag is None:
			self.generate_stem()
			return

		if self.metadatafile.tag.title:
			self.title = self.metadatafile.tag.title
		if self.metadatafile.tag.artist:
			self.artist = self.metadatafile.tag.artist
		if self.metadatafile.tag.album:
			self.album = self.metadatafile.tag.album
		if self.metadatafile.tag.track_num:
			self.tracknum = self.metadatafile.tag.track_num[0]
		if self.metadatafile.tag.lyrics:
			self.lyrics = self.metadatafile.tag.lyrics[0].text

			self.lyrics_cues = parse_embedded_srt(self.lyrics)

			if self.lyrics_cues:
				self.lyrics_format = "srt"

		self.generate_stem()

		if hasattr(self.metadatafile.tag, "images") and self.metadatafile.tag.images:
			self.cover = self.metadatafile.tag.images[0].image_data
			self.save_cover(COVERS_DIRECTORY)

	def generate_stem(self):
		title = self.sanitize_filename_component(self.title)
		artist = self.sanitize_filename_component(self.artist)
		album = self.sanitize_filename_component(self.album)
		self.stem = f"{title} ({artist} - {album})"

	def save_cover(self, directory: Path):
		directory = Path(directory)
		directory.mkdir(parents=True, exist_ok=True)

		if self.cover is not None:
			extension = self.metadatafile.tag.images[0].mime_type.split("/")[-1]
			self.coverfile = f"{self.stem}.{extension}"
			# print(self.coverfile)
			path = directory / self.coverfile

			try:
				with open(path, "wb") as f:
					f.write(self.cover)
			except OSError as exc:
				raise ValueError(f"Invalid cover path: {path}") from exc

	def play(self):
		self._ensure_audio_loaded()

		if self.playing:
			if self.paused:
				pygame.mixer.unpause()
				self.paused = False

			return self
		elif pygame.mixer.get_busy():
			pygame.mixer.stop()

		self.audio.play()
		self.playing = True
		return self

	def _ensure_audio_loaded(self):
		if self.audio is None:
			self.audio = pygame.mixer.Sound(str(self.path))
			if self.duration <= 0:
				self.duration = float(self.audio.get_length())

	def pause(self):
		if self.paused:
			return self

		if pygame.mixer.get_busy():
			pygame.mixer.pause()
			self.paused = True

		return self

	def set_volume(self, volume):
		self._ensure_audio_loaded()
		self.audio.set_volume(min(1.0, max(0.0, float(volume))))
		return self

	def stop(self):
		if self.audio is not None:
			self.audio.stop()
		self.playing = False
		self.paused = False
		return self

	def __repr__(self):
		return f"<Song title='{self.title}' artist='{self.artist}' album='{self.album}'{ ' playing' if self.playing else ' paused' if self.paused else ''}>"  # noqa
