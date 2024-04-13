from IPython.display import display, HTML
import polars as pl

pl.Config(
	fmt_str_lengths = 50,
	tbl_rows = 50,
	tbl_cols = 50,
)

def print_df(df: pl.DataFrame, title=None):
	html = df._repr_html_()
	if title:
		html = f"<h2>{title}</h2>" + html
	display(HTML(html))

def describe(df: pl.DataFrame, title=None):
	print_df(df.describe(), f"{title} - describe")
	for col in df.select(pl.col(pl.Categorical), pl.col(pl.Enum), pl.col(pl.Boolean)):
		print_df(col.value_counts().sort("count", descending=True), f"{title} - {col.name} - value_counts")
