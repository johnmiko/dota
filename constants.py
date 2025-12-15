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

SCORES_ALL_COLS_CSV_FILE = f'{TEXT_DIR}/scores_all_cols.csv'
SCORES_CSV_FILE = f'{TEXT_DIR}/scores.csv'
YOUTUBE_CSV_FILE = f'{TEXT_DIR}/scores_and_urls.csv'
HISTORIC_FILE = f'{TEXT_DIR}/historic.csv'
LATEST_HISTORIC_FILE = f'{TEXT_DIR}/last_6_months.csv'
ALREADY_WATCHED_FILE = f'{TEXT_DIR}/already_watched.txt'
LAST_GOT_HIGHLIGHT_VIDEOS = f'{TEXT_DIR}/last_got_highlight_videos.txt'
LAST_RUN_FILE = f'{TEXT_DIR}/last_run.json'
HIGHLIGHT_VIDEOS = f'{TEXT_DIR}/highlight_videos.csv'
SCORES_NO_HIGHLIGHTS = f'{TEXT_DIR}/scores_no_highlights.csv'
TEAM_NAMES_FILE = f'{TEXT_DIR}/team_names.csv'
DATE_STR_FORMAT = '%Y-%m-%d:%H:%M:%S'
TEAMS_I_LIKE = ['lgd', 'boom esports',
                'Team Spirit',
                'Gaimin Gladiators',
                'LGD Gaming',
                'Azure Ray',
                'Team Liquid',
                'BetBoom Team',
                'nouns',
                'Virtus pro',
                'TSM',
                '9Pandas',
                'Talon Esports',
                'Entity',
                'Shopify Rebellion',
                'Evil Geniuses',
                'Keyd Stars',
                'Tundra Esports',
                'Team SMG',
                'Thunder Awaken',
                'beastcoast',
                'Quest'
                'xtreme gaming',
                'invictus',
                'Team Spirit',
                'Natus Vincere'
                'MOUZ',
                'Virtus.pro',
                'HEROIC',
                'Team Falcons']
# Just using highlights score, but just been watching whole games
redo_historic_scores = os.getenv("REDO_HISTORIC_SCORES", "False")
if (redo_historic_scores != "True") and (redo_historic_scores != "False"):
    raise ValueError("REDO_HISTORIC_SCORES must be True or False")
REDO_HISTORIC_SCORES = redo_historic_scores == "True"  # convert to bool
HIGHLIGHTS_SCORE_COLS = ['fight_%_of_game', 'interesting_score', 'days_ago_score', 'good_team_playing_score']
WHOLE_GAME_SCORE_COLS = ['kills_per_min_score', 'swing_score', 'fight_%_of_game', 'days_ago_score',
                         'good_team_playing_score']
# to do, not implemented
# SERIES_SCORE_COLS = ['kills_per_min_score', 'swing_score', 'fight_%_of_game', 'days_ago_score',
#                          'good_team_playing_score']

TEAM_ABBR = {'betboom': 'bb',
             'gaimin gladiators': 'gg',
             'evil geniuses': 'eg'}
