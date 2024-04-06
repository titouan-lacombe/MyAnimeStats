from datetime import time
import polars as pl

class NextReleases:
	def get(user_animes: pl.LazyFrame):
		return user_animes.filter(
			(pl.col("user_watch_status") == "Plan to Watch") & (pl.col("air_status") == "Not yet aired")
		).sort("air_start", nulls_last=True).select(
			"title",
			# "air_start",
			# "air_time",
			"air_tz",
			datetime = pl.col("air_start").dt.combine(pl.col("air_time").replace(None, time(0, 0))),
			# text = pl.format(
			# 	"{} at {} ({})",
			# 	pl.col("air_start").dt.to_string("%A %d %B %Y"),
			# 	pl.col("air_time").dt.to_string("at %H:%M"),
			# 	pl.col("air_tz"),
			# ),
		)
