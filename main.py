from constants import LAST_FETCHED_DOTA_FILE
from game_has_highlights import find_games_without_highlights
from get_and_score_func import fetch_dota_data_from_api, get_and_score_func
from utils import should_run, last_ran, update_df_watched

last_ran("C:/Users/johnm/ccode/dota/last_ran.txt")
if should_run(LAST_FETCHED_DOTA_FILE, 4):
    fetch_dota_data_from_api()
# if should_run(LAST_GOT_HIGHLIGHT_VIDEOS, 8):
#     get_latest_videos_from_channel()
get_and_score_func()
update_df_watched()
df_no_highlights = find_games_without_highlights()
print(df_no_highlights.head(50).to_string())
print("finished")
