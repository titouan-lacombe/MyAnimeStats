import pytz
from datetime import datetime, time, timedelta
import polars as pl

WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

class Schedule:
	def get(user_animes: pl.LazyFrame):
		return user_animes.filter(
			(pl.col("user_watch_status") == "Watching") & (pl.col("air_status") == "Currently Airing")
		).select(
			"title",
			"air_day",
			"air_time",
			"air_tz",
		)

	def __init__(self, schedule: dict[str, list[dict[str, any]]]):
		self.schedule = schedule

	def get_dt(week_day: str, time: time, from_tz_str: str, to_tz_str: str):
		"Get the datetime for the given week day and time in the user's timezone"
		
		to_tz = pytz.timezone(to_tz_str)
		from_tz = pytz.timezone(from_tz_str)

		# Get start of the week
		now = datetime.now(from_tz)
		start_of_week = now.date() - timedelta(days=now.weekday())

		# Get the day and time
		day_num = WEEK_DAYS.index(week_day)
		air_at = datetime.combine(start_of_week + timedelta(days=day_num), time)

		# Localize the datetime to the JST timezone
		air_at = from_tz.localize(air_at)

		# Normalize the datetime to handle daylight saving time transitions
		air_at = from_tz.normalize(air_at)

		# Convert the datetime to the local timezone
		return air_at.astimezone(to_tz)

	# Finish building the schedule with the user timezone
	def from_df(schedule_df: pl.DataFrame):
		default_tz = "Asia/Tokyo"
		fake_user_tz = "Europe/Paris"

		# Build the schedule from the filtered animes
		schedule = {day: [] for day in WEEK_DAYS}
		for row in schedule_df.rows(named=True):
			dt: datetime = Schedule.get_dt(row["air_day"], row["air_time"], row.get("air_tz", default_tz), fake_user_tz)
			air_day = dt.strftime("%A")
			schedule[air_day].append({"title": row["title"], "datetime": dt})
		
		# Sort the schedule days by time of airing
		for animes in schedule.values():
			animes.sort(key=lambda x: x["datetime"])

		return Schedule(schedule)

	def _repr_html_(self):
		max_animes = max(len(animes) for animes in self.schedule.values())

		# Start the table and add the header row
		html = "<h3>Schedule</h3>"
		html += "<table><tr>"
		for day in WEEK_DAYS:
			html += f"<th>{day}</th>"
		html += "</tr>"

		# Add rows for each time slot
		for i in range(max_animes):
			html += "<tr>"
			for day in WEEK_DAYS:
				if i < len(self.schedule[day]):
					anime = self.schedule[day][i]
					html += f"<td>{anime['datetime'].strftime('%H:%M')} - {anime['title']}</td>"
				else:
					html += "<td></td>"  # Empty cell if no anime at this index for the day
			html += "</tr>"
		html += "</table>"

		return html
