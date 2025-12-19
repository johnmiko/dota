from logging import getLogger

import pandas as pd
import requests

from constants_old import TEAM_NAMES_FILE, HISTORIC_FILE, LATEST_HISTORIC_FILE

logger = getLogger(__name__)


def get_team_names_and_ranks_from_api():
    # https://docs.opendota.com#tag/teams
    # ?page=1
    teams_url = 'https://api.opendota.com/api/teams'
    logger.info("fetching team names and ranks")
    r = requests.get(teams_url)
    teams_raw = r.json()
    df_teams = pd.DataFrame(teams_raw)
    df_teams = df_teams.sort_values(by='rating', ascending=False)
    # match_id seems to be null for teams that do not exist anymore (example optic gaming)
    df_teams = df_teams[~df_teams["match_id"].isna()]
    return df_teams


def get_team_names_and_ranks_from_api_and_save_locally():
    df_teams = get_team_names_and_ranks_from_api()
    df_teams.to_csv(TEAM_NAMES_FILE, index=False, header=True)


DEFAULT_QUERY = f"""SELECT * 
    FROM matches
    JOIN leagues using(leagueid)
    WHERE name not like '%Division II%'
    AND leagues.TIER in ('professional','premium') 
    ORDER BY matches.start_time DESC
    LIMIT 1000"""


def fetch_dota_data_from_api(sql_query=DEFAULT_QUERY):
    # fetches data from opendota API and update the rolling 6 month file
    url = f"""https://api.opendota.com/api/explorer?sql={sql_query}"""
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        logger.error(r.text)
    matches = r.json()['rows']
    df = pd.DataFrame(matches)
    return df


def fetch_dota_data_from_api_and_save_locally(sql_query=DEFAULT_QUERY):
    # fetches data from opendota API and update the rolling 6 month file
    df_new = fetch_dota_data_from_api(sql_query)
    df_raw = pd.read_csv(LATEST_HISTORIC_FILE)
    df = pd.concat([df_new, df_raw])
    df = df.drop_duplicates('match_id')
    df = df[df['start_time'] >= (pd.Timestamp.now() - pd.DateOffset(months=4)).timestamp()]
    df.to_csv(LATEST_HISTORIC_FILE, index=False, header=True)


def update_historic_file():
    df_raw = pd.read_csv(HISTORIC_FILE)
    latest_timestamp = df_raw["start_time"].max()
    sql_query = f"""SELECT * 
    FROM matches
    JOIN leagues using(leagueid)
    WHERE name not like '%Division II%'
    AND leagues.TIER in ('professional','premium')
    AND matches.start_time > {latest_timestamp} 
    ORDER BY matches.start_time DESC
    LIMIT 4000"""
    url = f"""https://api.opendota.com/api/explorer?sql={sql_query}"""
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        logger.error(r.text)
    matches = r.json()['rows']
    if not matches:
        logger.info("no new matches found, not updating historic file")
        return
    df_new = pd.DataFrame(matches)
    df = pd.concat([df_new, df_raw])
    df = df.drop_duplicates('match_id')
    df.to_csv(HISTORIC_FILE, index=False, header=True)
