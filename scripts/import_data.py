"""Recreate the demonstration SQLite database from the supplied CSV data."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from database import DATABASE_PATH, initialise_database  # noqa: E402


if DATABASE_PATH.exists():
    DATABASE_PATH.unlink()
initialise_database()
print(f"База данных создана: {DATABASE_PATH}")

