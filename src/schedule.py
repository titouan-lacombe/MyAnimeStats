import datetime, pytz
from typing import List, Dict
import pandas as pd
from collections import defaultdict
from dateutil.tz import tzlocal
from pathlib import Path
from .log import logger

log = logger.getChild(__name__)

# Constants
DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
data = Path('data')
jst_tz = pytz.timezone('Asia/Tokyo')

def get_watching_animes(animes: List[Dict]) -> List[Dict]:
    """Returns the animes that are currently airing and being watched by the user."""
    return [anime for anime in animes if anime['airing'] and anime['my_status'] == 'Watching']

def convert_to_local_time(day_str: str, time_str: str) -> datetime.datetime:
    """Converts the given day and time in UTC to local time."""
    now = datetime.datetime.now(tzlocal())

    # Adjust today's date to the start of the current week (Monday)
    start_of_week = now.date() - datetime.timedelta(days=now.weekday())

    # Get the day and time of the anime broadcast
    day_num = DAYS_OF_WEEK.index(day_str.rstrip('s'))  # Remove 's' from the end of the day to make it singular
    time = datetime.time.fromisoformat(time_str)

    # Create a full datetime for the anime broadcast
    broadcast = datetime.datetime.combine(start_of_week + datetime.timedelta(days=day_num), time)

    # Localize the datetime to the JST timezone
    broadcast = jst_tz.localize(broadcast)

    # Normalize the datetime to handle daylight saving time transitions
    broadcast = jst_tz.normalize(broadcast)

    # Convert the datetime to the local timezone
    return broadcast.astimezone(tzlocal())

def create_schedule(schedule: List[Dict]) -> pd.DataFrame:
    """Creates a DataFrame from the given schedule sorted by day of the week and time."""
    df_schedule = pd.DataFrame(schedule)

    # If the DataFrame is empty, return an empty DataFrame
    if df_schedule.empty:
        return None

    # Sort the DataFrame by day of the week and time
    df_schedule = df_schedule.sort_values(['day', 'time'])

    # Group the DataFrame by day and create the schedule for each day
    schedule_by_day = defaultdict(list)
    for _, row in df_schedule.iterrows():
        schedule_by_day[row['day']].append(f"{row['time'].strftime('%H:%M')} {row['title']}")

    # Find the maximum number of animes airing on a single day
    max_len = max(len(v) for v in schedule_by_day.values())

    # Extend the lists of other days with empty strings until they match the maximum length
    for day in DAYS_OF_WEEK:
        schedule_by_day[day].extend([''] * (max_len - len(schedule_by_day[day])))

    # Create a DataFrame for the schedule
    df_schedule_by_day = pd.DataFrame(dict(schedule_by_day))
    df_schedule_by_day = df_schedule_by_day.reindex(DAYS_OF_WEEK, axis=1)  # Reorder the columns by day of the week

    return df_schedule_by_day


def get_schedule(animes):
    # Extract airing schedule for the animes being watched
    schedule = []
    for anime in get_watching_animes(animes):
        if 'broadcast' in anime and 'day' in anime['broadcast'] and 'time' in anime['broadcast']:
            broadcast_local = convert_to_local_time(anime['broadcast']['day'], anime['broadcast']['time'])

            title = anime.get('title_english') or anime.get('title')  # Default to 'title' if 'title_english' is None

            schedule.append({
                'title': title,
                'day': DAYS_OF_WEEK[broadcast_local.weekday()],
                'time': broadcast_local.time()
            })

    # Create the schedule DataFrame
    df_schedule = create_schedule(schedule)

    return df_schedule
