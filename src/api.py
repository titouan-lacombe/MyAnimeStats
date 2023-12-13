import aiohttp

from .load_list import load_web_list, load_xml_list
from .complete_anime import complete_animes
from .franchises import get_franchises
from .schedule import get_schedule
from .staff import get_staff

# Get franchises from input
# export_file: File like object containing the MAL XML export
# username: string containing the MAL username
async def my_anime_stats(export_file=None, username=None):
	# Load anime list
	if export_file is not None:
		print("Loading anime list from MAL XML export")
		animes = load_xml_list(export_file)
	elif username is not None:
		print("Loading anime list from MAL username")
		async with aiohttp.ClientSession() as session:
			animes = await load_web_list(username, session)
	else:
		raise ValueError("Either export_file or username must be specified")
	
	# Complete anime data
	print("Completing animes data with data from MAL")
	animes = await complete_animes(animes)
	
	# Get staff
	print("Getting staff data from MAL")
	staff = await get_staff(animes)

	# Compute franchises
	print("Computing franchises")
	franchises = get_franchises(animes)

	# Get schedule
	print("Computing schedule")
	schedule = get_schedule(animes)

	return animes, franchises, schedule, staff
