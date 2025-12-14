from constants import LAST_RUN_FILE
from dota.api import get_team_names_and_ranks_from_api, fetch_dota_data_from_api
from dota.run_tracker import RunTracker
from game_has_highlights import find_games_without_highlights
from get_and_score_func import get_and_score_func
from utils import update_df_watched

run_tracker = RunTracker(LAST_RUN_FILE)

if run_tracker.should_run("last_fetched_data", 4):
    # adds new data to RAW_FILE
    fetch_dota_data_from_api()
if run_tracker.should_run("last_got_team_names", 4):
    get_team_names_and_ranks_from_api()

get_and_score_func()
update_df_watched()
df_no_highlights = find_games_without_highlights()
print(df_no_highlights.head(50).to_string())
print("finished")
