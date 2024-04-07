import os
from IPython.display import display, HTML
import polars as pl

os.environ["POLARS_FMT_MAX_ROWS"] = "50"
os.environ["POLARS_FMT_MAX_COLS"] = "50"
pl.Config(fmt_str_lengths=50)

def print_df(df: pl.DataFrame, title=None):
	html = df._repr_html_()
	if title:
		html = f"<h3>{title}</h3>" + html
	display(HTML(html))
