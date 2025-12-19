import ast
import json
from collections import Counter
from datetime import datetime
from logging import getLogger

import numpy as np
import pandas as pd

from constants_old import TEAM_NAMES_FILE
from dota.api import get_team_names_and_ranks_from_api

logger = getLogger(__name__)


def calc_min_in_lead(df, i, radiant_gold_adv):
    # Find the number of minutes the team was in the lead before they won
    if not radiant_gold_adv:
        df.loc[i, 'min_in_lead'] = 0
        return df
    radiant_gold_adv = np.array(radiant_gold_adv)
    sign_changes = list((np.diff(np.sign(radiant_gold_adv)) != 0) * 1)
    sign_changes.reverse()
    try:
        # The values of the list are at minute points, so can just get the index to know how many minutes
        df.loc[i, 'min_in_lead'] = sign_changes.index(1)
    except ValueError:
        # value error will occur if a team was winning the entire game, then no sign change will have occurred
        try:
            radiant_always_winning = (df.loc[i, 'radiant_win'] & (radiant_gold_adv[-1] > 0))
            dire_always_winning = ((df.loc[i, 'radiant_win'] == False) & (radiant_gold_adv[-1] < 0))
            winning_entire_game = radiant_always_winning | dire_always_winning
            if winning_entire_game:
                df.loc[i, 'min_in_lead'] = len(sign_changes)
            else:
                df.loc[i, 'min_in_lead'] = 0
        except TypeError:
            df.loc[i, 'min_in_lead'] = 0
    return df


def calc_max_gold_swing(df, i, radiant_gold_adv):
    # want to find the largest change in values from max value to any value after that
    # We choose a 10-minute window because it's not interesting if a team is up then another team slowly gets the lead after?
    # improvement - also check the swing over the entire game, see what that gives
    max_swing = 0
    skip_first_x_minutes = 10
    for j in range(skip_first_x_minutes, len(radiant_gold_adv) - 1):
        # Find max net worth change that has occurred in the past 10 minutes
        # Set value to 11 instead of 10 because of indexing
        max_window = 11
        indices_left = len(radiant_gold_adv[j + 1:]) + 1
        window = indices_left if indices_left < max_window else max_window
        val = radiant_gold_adv[j]
        if abs(val) < 5000:
            continue
        if val > 0:
            min_val = min(radiant_gold_adv[j + 1:j + window])
            if min_val < 0:
                min_val = 0
            swing = val - min_val
            # dif = val - min(radiant_gold_adv[j + 1:j + max_window])
        else:
            try:
                max_val = max(radiant_gold_adv[j + 1:j + window])
            except:
                a = 1
            if max_val > 0:
                max_val = 0
            swing = val - max_val

        if abs(swing) > max_swing:
            max_swing = abs(swing)
    df.loc[i, 'swing'] = max_swing
    return df


def calc_game_num(df):
    df.sort_values('date').groupby('series_id')
    df['game_num'] = df.groupby('series_id')['date'].rank('min')
    return df


def calc_teamfight_stats(df, i):
    # looks like this - [{'start': 2060, 'end': 2133, 'last_death': 2118, 'deaths': 8, ...
    # or is NaN
    teamfights = df.loc[i, 'teamfights']
    if type(teamfights) == str:
        # convert to list
        teamfights = ast.literal_eval(teamfights)
    if (type(teamfights) != list) and pd.isna(teamfights):
        df.loc[i, 'first_fight_at'] = "30"
        df.loc[i, 'fight_%_of_game'] = "0"
        df.loc[i, 'avg_fight_length'] = "0"
        return df
    # num_teamfights = len(teamfights)
    secs_of_fighting = 0
    first_fight_at_in_secs = 100000
    for fight in teamfights:
        secs_of_fighting += fight['end'] - fight['start']
        if fight['start'] < first_fight_at_in_secs:
            first_fight_at_in_secs = fight['start']
    # df['first_fight_at'] = df['first_fight_at'].astype('string')
    # Only count since the first fight time because that's the time I will start watching
    df.loc[i, 'first_fight_at'] = str(str(first_fight_at_in_secs // 60) + ':' + str(first_fight_at_in_secs % 60))
    df.loc[i, 'fight_%_of_game'] = secs_of_fighting / (df.loc[i, 'duration'] - first_fight_at_in_secs)
    num_teamfights = len(teamfights) if len(teamfights) > 0 else 1
    df.loc[i, 'avg_fight_length'] = secs_of_fighting / num_teamfights
    return df


def calc_time_ago(df):
    df['start_time'] = df['start_time'].fillna(0)
    df['date'] = pd.to_datetime(df['start_time'], unit='s')
    # Not accounting for UTC
    # Improvement, remove the time_ago column completely and just use days_ago, then add the string on the frontend
    df2 = pd.DataFrame()
    df2['dif'] = datetime.now() - df['date']
    df2['time_ago'] = None
    df2['days_ago'] = None
    df2.loc[df2['dif'].dt.days < 7, 'time_ago'] = df2['dif'].dt.days.astype(str) + ' days ago'
    df2.loc[df2['dif'].dt.days < 7, 'days_ago'] = df2['dif'].dt.days.astype(str)
    df2.loc[df2['dif'].dt.days == 0, 'time_ago'] = (df2['dif'].dt.seconds / 3600).astype(int).astype(str) + ' hours ago'
    df2.loc[df2['dif'].dt.days == 0, 'days_ago'] = (df2['dif'].dt.seconds / 3600).astype(int).astype(str)
    df2.loc[df2['dif'].dt.days >= 7, 'time_ago'] = (df2['dif'].dt.days / 7).astype(int).astype(str) + ' weeks ago'
    df2.loc[df2['dif'].dt.days >= 7, 'days_ago'] = (df2['dif'].dt.days).astype(int).astype(str)
    df2['months_ago'] = ((df2['dif']) / np.timedelta64(4, 'W')).astype(int)
    df2.loc[df2['months_ago'] > 0, 'time_ago'] = df2['months_ago'].astype(str) + ' months ago'
    df2.loc[df2['months_ago'] > 0, 'days_ago'] = df2['months_ago'].astype(str)
    df['time_ago'] = df2['time_ago']
    return df


# def get_team_names_and_ranks(df):
#     df = df.copy()
#
#     # If df has a 'name' column and it's the tournament, lock that in first
#     if "name" in df.columns and "tournament" not in df.columns:
#         df = df.rename(columns={"name": "tournament"})
#
#     df_teams = pd.read_csv(TEAM_NAMES_FILE).reset_index(names="rank")
#
#     # dire
#     dire = df_teams.rename(columns={
#         "team_id": "dire_team_id",
#         "name": "dire_team_name",
#         "rank": "dire_team_rank",
#     })[["dire_team_id", "dire_team_name", "dire_team_rank"]]
#
#     # radiant
#     rad = df_teams.rename(columns={
#         "team_id": "radiant_team_id",
#         "name": "radiant_team_name",
#         "rank": "radiant_team_rank",
#     })[["radiant_team_id", "radiant_team_name", "radiant_team_rank"]]
#
#     df = df.merge(dire, on="dire_team_id", how="left", validate="m:1")
#     df = df.merge(rad, on="radiant_team_id", how="left", validate="m:1")
#     return df


def get_team_names_and_ranks(df, df_teams=None):
    if df_teams is None:
        df_teams = get_team_names_and_ranks_from_api()
    df_teams["rank"] = df_teams.index + 1
    df = df.merge(df_teams[['team_id', 'name', 'rank']], how='left', left_on='radiant_team_id', right_on='team_id')
    df = df.merge(df_teams[['team_id', 'name', 'rank']], how='left', left_on='dire_team_id', right_on='team_id')
    # df = df.rename(columns={"name_x": "radiant_team_name", "rank_x": "radiant_team_rank", "name_y": "dire_team_name",
    #                         "rank_y": "dire_team_rank"})
    df = df.rename(columns={"rank_x": "radiant_team_rank",
                            "rank_y": "dire_team_rank"})
    df['radiant_team_name'] = df['name_x']
    df['dire_team_name'] = df['name_y']
    df = df.drop(columns=['name_x', 'name_y', 'team_id_x', 'team_id_y'])
    return df


def create_title(df):
    # Remove text after 'presented' and/or 'powered'
    df[['radiant_team_name', 'dire_team_name', 'tournament']] = \
        df[['radiant_team_name', 'dire_team_name', 'tournament']].fillna('???')
    df['game_num'] = df['game_num'].fillna(-1)
    df['tournament'] = df['tournament'].str.split('presented').str[0].str.split('powered').str[0].str.strip()
    df['title'] = df['radiant_team_name'] + ' vs ' + df['dire_team_name'] + ' game ' + df['game_num'].astype(
        int).astype(str) + ' ' + df['tournament']
    return df


def calc_gold_lead_is_small(df, i, radiant_gold_adv):
    # radiant gold advantage is a list containing how much gold radiant was winning by at minute intervals
    # ex: [0, -16, -281, -378, -262, -576, -798, -916, -954, -1345, -2055, -1913...
    if not radiant_gold_adv:
        df.loc[i, 'lead_is_small'] = 0
        return df
    # Number of minutes where the lead was less than 5000 gold
    game_length_in_minutes = len(radiant_gold_adv)
    # If the game was less than 5 minutes long, don't count it
    start_index = game_length_in_minutes if len(radiant_gold_adv) < 5 else 5
    lead_is_small = sum(abs(i) < 5000 for i in radiant_gold_adv[start_index:])
    # Percentage of minutes where the lead was less than 5000 gold
    pct_lead_small = lead_is_small / len(radiant_gold_adv)
    df.loc[i, 'lead_is_small'] = pct_lead_small
    return df


def add_total_objectives_cols(df, i):
    row = df.loc[i]
    if type(row["objectives"]) == str:
        objectives = ast.literal_eval(row["objectives"])
    else:
        objectives = row["objectives"]
    # catches the case where objectives is NaN
    if type(objectives) == list:
        totals = Counter(d['type'] for d in objectives)
        # TODO: Not checking if a new objective exists, want to know if the data has changed
        for k, v in totals.items():
            df.loc[i, k] = v
    return df


def calculate_all_game_statistics(df):
    df['total_kills'] = df['radiant_score'] + df['dire_score']
    df['duration_min'] = (df['duration'] / 60).round()
    df = df.rename(columns={"name": "tournament"})
    df = get_team_names_and_ranks(df)
    df = calc_time_ago(df)
    df = calc_game_num(df)
    df = create_title(df)
    df['days_ago'] = (df['date'] - datetime.now()).dt.days
    df[['swing', 'fight_%_of_game', 'lead_is_small', 'avg_fight_length']] = None

    for i, row in df.iterrows():
        # radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        teamfights = df.loc[i, 'teamfights']
        df = add_total_objectives_cols(df, i)
        if teamfights is None:
            df.loc[i, 'first_fight_at'] = 10000
            df.loc[i, 'fight_%_of_game'] = 0
            df.loc[i, 'avg_fight_length'] = 0
        else:
            df = calc_teamfight_stats(df, i)
        radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        # if np.na or (None or [])
        if (type(radiant_gold_adv) != list and pd.isna(radiant_gold_adv)) or (not radiant_gold_adv):
            df.loc[i, 'min_in_lead'] = 100
            df.loc[i, 'swing'] = 0
            df.loc[i, 'lead_is_small'] = 0

        else:
            radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
            if type(radiant_gold_adv) == str:
                try:
                    radiant_gold_adv = ast.literal_eval(df.loc[i, 'radiant_gold_adv'])
                except:
                    radiant_gold_adv = json.loads(df.loc[i, 'radiant_gold_adv'])
            df = calc_min_in_lead(df, i, radiant_gold_adv)
            df = calc_max_gold_swing(df, i, radiant_gold_adv)
            df = calc_gold_lead_is_small(df, i, radiant_gold_adv)
    df['swing'] = df['swing'].astype(int)
    df['lead_is_small'] = df['lead_is_small'].astype(float).round(2)
    df['min_in_lead'] = df['min_in_lead'].astype(int).round(2)
    df['fight_%_of_game'] = df['fight_%_of_game'].astype(float).round(2)
    df['avg_fight_length'] = df['avg_fight_length'].astype(float).round(2)
    return df
