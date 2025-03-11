from pathlib import Path

cwd = Path()
data = cwd / "data"
src = cwd / "src"
static = src / "static"
anime_db_path = data / "anime_db.parquet"
manga_db_path = data / "manga_db.parquet"
characters_db_path = data / "characters_db.parquet"
people_db_path = data / "people_db.parquet"

datasets = [anime_db_path, manga_db_path, characters_db_path, people_db_path]
