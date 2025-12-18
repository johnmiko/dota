from constants import LAST_FETCHED_DOTA_FILE
from dota.game_has_highlights import find_games_without_highlights
from dota.get_and_score_func import get_and_score_func
from dota.api import fetch_dota_data_from_api
from dota.utils import should_run, last_ran, update_df_watched

last_ran("C:/Users/johnm/ccode/dota/last_ran.txt")
if should_run("last_fetched_data", 4):
    # adds new data to HISTORIC_FILE
    sql_query = """
select match_id, start_time, avg_rank_tier, duration, radiant_win
from public_matches
where avg_rank_tier is not null
  and avg_rank_tier <= 15
order by start_time desc
limit 50

    """
    fetch_dota_data_from_api(sql_query=sql_query)
# if should_run(LAST_GOT_HIGHLIGHT_VIDEOS, 8):
#     get_latest_videos_from_channel()
get_and_score_func()
update_df_watched()
df_no_highlights = find_games_without_highlights()
print(df_no_highlights.head(50).to_string())
print("finished")
