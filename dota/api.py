from logging import getLogger

import pandas as pd
import requests

from constants import TEAM_NAMES_FILE, RAW_FILE, LATEST_RAW_FILE

logger = getLogger(__name__)


def get_team_names_and_ranks_from_api():
    teams_url = 'https://api.opendota.com/api/teams?limit=200'
    logger.info("fetching team names and ranks")
    r = requests.get(teams_url)
    teams_raw = r.json()
    df_teams = pd.DataFrame(teams_raw)
    df_teams = df_teams[~df_teams["match_id"].isna()]
    # maybe better to write just the json data to file, not sure
    df_teams.to_csv(TEAM_NAMES_FILE, index=False, header=True)


DEFAULT_QUERY = f"""SELECT * 
    FROM matches
    JOIN leagues using(leagueid)
    WHERE name not like '%Division II%'
    ORDER BY matches.start_time DESC
    LIMIT 1000"""


def fetch_dota_data_from_api(sql_query=DEFAULT_QUERY):
    # fetches data from opendota API and updates the raw file
    update_data = True
    if update_data:
        pass
    url = f"""https://api.opendota.com/api/explorer?sql={sql_query}"""
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        print(r.text)
    matches = r.json()['rows']
    df_new = pd.DataFrame(matches)
    df_raw = pd.read_csv(RAW_FILE)
    df = pd.concat([df_new, df_raw])
    df = df.drop_duplicates('match_id')
    df.to_csv(RAW_FILE, index=False, header=True)
    df2 = df[df['start_time'] >= (pd.Timestamp.now() - pd.DateOffset(months=6)).timestamp()]
    df2.to_csv(LATEST_RAW_FILE, index=False, header=True)
