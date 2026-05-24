from pathlib import Path
import socket
import json
import os

LEGACY_USER_DATA_DIRECTORY = Path(__file__).parent / "data"
if os.name == "nt":
	default_data_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
else:
	default_data_root = Path.home()

USER_DATA_DIRECTORY = default_data_root / "mu_player"
USER_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

COVERS_DIRECTORY = USER_DATA_DIRECTORY / "covers"
COVERS_DIRECTORY.mkdir(parents=True, exist_ok=True)

DEFAULT_MUSIC_FOLDER = r"C:\Users\after\OneDrive\Music\good kid"
DEFAULT_APP_CONFIG = {
	"music_folder": DEFAULT_MUSIC_FOLDER,
	"show_cover_art": True,
	"default_volume": 100,
	"auto_play_on_open": True,
	"open_browser_on_start": True,
}

APP_CONFIG_PATH = USER_DATA_DIRECTORY / "config.json"
LEGACY_APP_CONFIG_PATH = LEGACY_USER_DATA_DIRECTORY / "config.json"


def _to_bool(value, default):
	if isinstance(value, bool):
		return value

	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in {"1", "true", "yes", "on"}:
			return True
		if normalized in {"0", "false", "no", "off"}:
			return False

	return default


def _normalize_app_config(config):
	normalized = DEFAULT_APP_CONFIG.copy()

	if not isinstance(config, dict):
		return normalized

	normalized.update(config)

	music_folder = config.get("music_folder")
	if isinstance(music_folder, str) and music_folder.strip():
		normalized["music_folder"] = music_folder
	else:
		normalized["music_folder"] = DEFAULT_APP_CONFIG["music_folder"]

	show_cover_art = config.get("show_cover_art")
	normalized["show_cover_art"] = _to_bool(show_cover_art, DEFAULT_APP_CONFIG["show_cover_art"])

	auto_play_on_open = config.get("auto_play_on_open")
	normalized["auto_play_on_open"] = _to_bool(auto_play_on_open, DEFAULT_APP_CONFIG["auto_play_on_open"])

	open_browser_on_start = config.get("open_browser_on_start")
	normalized["open_browser_on_start"] = _to_bool(open_browser_on_start, DEFAULT_APP_CONFIG["open_browser_on_start"])

	default_volume = config.get("default_volume")
	if isinstance(default_volume, bool):
		default_volume = DEFAULT_APP_CONFIG["default_volume"]

	try:
		default_volume = int(default_volume)
	except (TypeError, ValueError):
		default_volume = DEFAULT_APP_CONFIG["default_volume"]

	normalized["default_volume"] = min(100, max(0, default_volume))

	return normalized


def save_app_config(config):
	normalized = _normalize_app_config(config)
	APP_CONFIG_PATH.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
	return normalized


def _read_json(path):
	try:
		return json.loads(path.read_text(encoding="utf-8"))
	except (json.JSONDecodeError, OSError):
		return None


def load_app_config():
	if APP_CONFIG_PATH.exists():
		config = _read_json(APP_CONFIG_PATH)
		if config is None:
			return save_app_config(DEFAULT_APP_CONFIG)
		return _normalize_app_config(config)

	if LEGACY_APP_CONFIG_PATH.exists():
		legacy_config = _read_json(LEGACY_APP_CONFIG_PATH)
		if legacy_config is not None:
			return save_app_config(legacy_config)

	return save_app_config(DEFAULT_APP_CONFIG)


def get_ip_address():
	try:
		hostname = socket.gethostname()
		ip = socket.gethostbyname(hostname)
	except socket.gaierror:
		hostname = None
		ip = None

	if ip == "127.0.0.1":
		ip = None

	return ip
