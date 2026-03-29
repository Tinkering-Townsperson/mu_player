from pathlib import Path
import socket

USER_DATA_DIRECTORY = Path(__file__).parent / "data"
USER_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

COVERS_DIRECTORY = USER_DATA_DIRECTORY / "covers"
COVERS_DIRECTORY.mkdir(parents=True, exist_ok=True)


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
