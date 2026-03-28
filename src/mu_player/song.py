import eyed3
from pathlib import Path
from .config import COVERS_DIRECTORY
import pygame

pygame.mixer.init()


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
			print(self.coverfile)
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

	def stop(self):
		if self.audio is not None:
			self.audio.stop()
		self.playing = False
		self.paused = False
		return self

	def __repr__(self):
		return f"<Song title='{self.title}' artist='{self.artist}' album='{self.album}'{ ' playing' if self.playing else ' paused' if self.paused else ''}>"  # noqa
