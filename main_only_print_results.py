from constants import LAST_RUN_FILE
from dota.api import get_team_names_and_ranks_from_api, fetch_dota_data_from_api
from dota.run_tracker import RunTracker
from get_and_score_func import get_and_score_func

run_tracker = RunTracker(LAST_RUN_FILE)

fetch_dota_data_from_api()
get_team_names_and_ranks_from_api()
get_and_score_func()
print("finished")
