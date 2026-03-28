from pathlib import Path

USER_DATA_DIRECTORY = Path(__file__).parent / "data"
USER_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

COVERS_DIRECTORY = USER_DATA_DIRECTORY / "covers"
COVERS_DIRECTORY.mkdir(parents=True, exist_ok=True)
