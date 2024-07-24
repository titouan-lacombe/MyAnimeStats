import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from common.filesystem import anime_db_path, characters_db_path, manga_db_path, people_db_path
from common.utils import set_page_config
from typing import Dict


set_page_config(
	layout="wide",
)

st.title("Dataset Import")

files = st.file_uploader(
	"Upload the MAL dataset",
	type=["parquet"],
	accept_multiple_files=True,
)

expected_files = {
	"anime_db.parquet": anime_db_path,
	"characters_db.parquet": characters_db_path,
	"manga_db.parquet": manga_db_path,
	"people_db.parquet": people_db_path,
}

def import_files(files: Dict[str, UploadedFile]):
	uploaded_files = set([file.name for file in files.values()])
	required_files = set(expected_files.keys())

	missing_files = required_files - uploaded_files
	if missing_files:
		st.error(f"Missing files: {missing_files}")
		return

	unexpected_files = uploaded_files - required_files
	if unexpected_files:
		st.error(f"Unexpected files: {unexpected_files}")
		return

	for name, path in expected_files.items():
		with path.open("wb") as f:
			while chunk := files[name].read(1024 * 1024):
				f.write(chunk)

	st.success("Files imported successfully")

if len(files) > 0:
	files = {file.name: file for file in files}
	import_files(files)
