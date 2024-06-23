from datetime import time, datetime
import polars as pl

class NextReleases:
	def get(user_animes: pl.LazyFrame, user_tz: str, now: datetime):
		# Patch since all animes are in JST (later we will use air_tz)
		animes_tz = "Asia/Tokyo"

		return user_animes.filter(
			(pl.col("user_watch_status") == "Plan to Watch")
			& (pl.col("air_status") == "Not yet aired")
			& (pl.col("air_start").is_not_null())
			& (pl.col("air_start").dt.date() >= now.date())
		).sort("air_start", nulls_last=True).with_columns(
			text = pl.col("air_start").dt.combine(pl.col("air_time").replace(
				None, time(0, 0))
			).dt.replace_time_zone(animes_tz).dt.convert_time_zone(
				user_tz
			).dt.to_string(
				"%A %d %B %Y at %H:%M"
			)
		).select("title_localized", "text").rename({
			"title_localized": "Title",
			"text": "Air Date",
		})
