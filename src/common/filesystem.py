from pathlib import Path

cwd = Path()
data = cwd / 'data'
src = cwd / 'src'
static = src / 'static'
anime_db_path = data / 'anime_db.parquet'
# anime_db_path = data / 'anime_db.franchise.parquet'
manga_db_path = data / 'manga_db.parquet'
character_db_path = data / 'character_db.parquet'
people_db_path = data / 'people_db.parquet'
