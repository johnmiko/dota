# In the process of refactoring, leave for now until we have all the references fixed
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

GLOBAL_LOG_LEVEL = logging.INFO
# PROJ_DIR = os.path.dirname(os.path.abspath(Path(__file__).parent))
PROJ_DIR = os.path.dirname(os.path.abspath(Path(__file__)))
DOTA_DIR = PROJ_DIR + '/'
TEXT_DIR = os.getenv("TEXT_DIR", "C:/Users/johnm/OneDrive/miscellaneous/ccode_files/dota/text")
LOCAL_TEX_DIR = f"{PROJ_DIR}/text/"
SCORES_ALL_COLS_FOR_EXCEL_CSV_FILE = f'{LOCAL_TEX_DIR}/scores_all_cols_for_excel.csv'
SCORES_ALL_COLS_CSV_FILE = f'{LOCAL_TEX_DIR}/scores_all_cols.csv'
SCORES_CSV_FILE = f'{LOCAL_TEX_DIR}/scores.csv'
YOUTUBE_CSV_FILE = f'{TEXT_DIR}/scores_and_urls.csv'
HISTORIC_FILE = f'{TEXT_DIR}/historic.csv'
LATEST_HISTORIC_FILE = f'{LOCAL_TEX_DIR}/last_6_months.csv'
ALREADY_WATCHED_FILE = f'{TEXT_DIR}/already_watched.txt'
LAST_GOT_HIGHLIGHT_VIDEOS = f'{LOCAL_TEX_DIR}/last_got_highlight_videos.txt'
LAST_RUN_FILE = f'{LOCAL_TEX_DIR}/last_run.json'
HIGHLIGHT_VIDEOS = f'{TEXT_DIR}/highlight_videos.csv'
SCORES_NO_HIGHLIGHTS = f'{TEXT_DIR}/scores_no_highlights.csv'
TEAM_NAMES_FILE = f'{LOCAL_TEX_DIR}/team_names.csv'
DATE_STR_FORMAT = '%Y-%m-%d:%H:%M:%S'
# Just using highlights score, but just been watching whole games
redo_historic_scores = os.getenv("REDO_HISTORIC_SCORES", "False")
if (redo_historic_scores != "True") and (redo_historic_scores != "False"):
    raise ValueError("REDO_HISTORIC_SCORES must be True or False")
REDO_HISTORIC_SCORES = redo_historic_scores == "True"  # convert to bool
TEAMS_I_LIKE = ['Team Liquid', 'Team Spirit', 'Tundra Esports', 'Team Falcons']
FINAL_SCORE_COLS = ['interesting_score', 'days_ago_score', 'good_team_playing_score', 'aegis_steals_score']
WHOLE_GAME_SCORE_COLS = ['swing_score', 'fight_%_of_game_score', 'days_ago_score',
                         'good_team_playing_score']
SCORES_COLS = ['match_id', 'title', 'time_ago', 'final_score', 'first_fight_at', 'tournament']
# to do, not implemented
# SERIES_SCORE_COLS = ['swing_score', 'fight_%_of_game_score', 'days_ago_score',
#                          'good_team_playing_score']

TEAM_ABBR = {'betboom': 'bb',
             'gaimin gladiators': 'gg',
             'evil geniuses': 'eg'}
