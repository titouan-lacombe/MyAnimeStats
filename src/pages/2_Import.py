import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
from common.filesystem import datasets
from common.utils import set_page_config
from typing import List


set_page_config(
	layout="wide",
)

st.title("MAL Datasets Importer")

files = st.file_uploader(
	"Upload files",
	type=["parquet"],
	accept_multiple_files=True,
)

def import_files(files: List[UploadedFile]):
	uploaded_names = set([file.name for file in files])
	expected_names = set([file.name for file in datasets])

	# Check if there are any unexpected files
	unexpected_files = uploaded_names - expected_names
	if unexpected_files:
		st.error(f"Unexpected files: {unexpected_files}")
		return

	# Download files
	files_map = {file.name: file for file in datasets}
	for file in files:
		with files_map[file.name].open("wb") as f:
			while chunk := file.read(1024 * 1024):
				f.write(chunk)

	st.success("Datasets imported successfully")

if len(files) > 0:
	import_files(files)

# Check if all datasets are present
missing_datasets = [file for file in datasets if not file.exists()]

if len(missing_datasets) == 0:
	st.success("All datasets are present, application is ready to use")
else:
	st.warning(
		"Some datasets are still missing:\n" +
		"\n".join([f"- {file.name}" for file in missing_datasets])
	)
