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
RAW_FILE = f'{TEXT_DIR}/raw.csv'
ALREADY_WATCHED_FILE = f'{TEXT_DIR}/already_watched.txt'
LAST_FETCHED_DOTA_FILE = f'{TEXT_DIR}/last_fetched_dota.txt'
LAST_GOT_HIGHLIGHT_VIDEOS = f'{TEXT_DIR}/last_got_highlight_videos.txt'
HIGHLIGHT_VIDEOS = f'{TEXT_DIR}/highlight_videos.csv'
SCORES_NO_HIGHLIGHTS = f'{TEXT_DIR}/scores_no_highlights.csv'
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
                'Team Spirit']
# Just using highlights score, but just been watching whole games
REDO_SCORES = False
HIGHLIGHTS_SCORE_COLS = ['fight_%_of_game', 'interesting_score', 'days_ago_score', 'good_team_playing_score']
WHOLE_GAME_SCORE_COLS = ['kills_per_min_score', 'swing_score', 'fight_%_of_game', 'days_ago_score',
                         'good_team_playing_score']
# to do, not implemented
# SERIES_SCORE_COLS = ['kills_per_min_score', 'swing_score', 'fight_%_of_game', 'days_ago_score',
#                          'good_team_playing_score']

TEAM_ABBR = {'betboom': 'bb',
             'gaimin gladiators': 'gg',
             'evil geniuses': 'eg'}
