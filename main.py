import logging
from logging import getLogger

import pandas as pd

from constants import LAST_RUN_FILE, SCORES_ALL_COLS_CSV_FILE, SCORES_COLS
from dota.api import get_team_names_and_ranks_from_api, fetch_dota_data_from_api, update_historic_file
from dota.get_and_score_func import get_and_score_func
from dota.run_tracker import RunTracker
from dota.utils import update_df_watched

logger = getLogger(__name__)

logging.basicConfig(level=logging.INFO)
run_tracker = RunTracker(LAST_RUN_FILE)

if run_tracker.should_run("update_historic", 23):
    update_historic_file()
if run_tracker.should_run("last_fetched_data", 1):
    fetch_dota_data_from_api()
if run_tracker.should_run("last_got_team_names", 1):
    get_team_names_and_ranks_from_api()

get_and_score_func()
update_df_watched()
df = pd.read_csv(SCORES_ALL_COLS_CSV_FILE)
logger.info(df[SCORES_COLS].head(100).to_string())
logger.info("finished")
