# https://overwolf.github.io/api/media/replays/auto-highlights
import ast
import json
from datetime import datetime
from logging import getLogger

import numpy as np
import pandas as pd

from calcs import calc_teamfight_stats, calc_gold_adv_rate, calc_gold_adv_std, calc_min_in_lead, \
    calc_max_gold_swing, calc_gold_lead_is_small, get_team_names_and_ranks, calc_time_ago, create_title, calc_game_num, \
    add_total_objectives_cols
from constants import SCORES_CSV_FILE, ALREADY_WATCHED_FILE, SCORES_ALL_COLS_CSV_FILE, \
    HIGHLIGHTS_SCORE_COLS, \
    RAW_FILE, TEAMS_I_LIKE, REDO_HISTORIC_SCORES, WHOLE_GAME_SCORE_COLS, LATEST_RAW_FILE
from score import linear_map

logger = getLogger(__name__)


def get_df_of_games_that_need_scored():
    if REDO_HISTORIC_SCORES:
        df_raw = pd.read_csv(RAW_FILE)
        logger.info("recalculating all scores")
        df = df_raw
    else:
        df_raw = pd.read_csv(LATEST_RAW_FILE)
        logger.info("only calculating scores for new games")
        df_scored = pd.read_csv(SCORES_ALL_COLS_CSV_FILE)
        df = df_raw[~df_raw["match_id"].isin(df_scored["match_id"])]
    return df


def clean_df_and_fill_nas(df):
    df['start_time'] = df['start_time'].fillna(0)
    df['date'] = pd.to_datetime(df['start_time'], unit='s')
    df['name'] = df['name'].fillna('')
    df = df[~df['name'].str.contains('Division II')]
    known_objectives = ['CHAT_MESSAGE_COURIER_LOST', 'CHAT_MESSAGE_FIRSTBLOOD', 'building_kill',
                        'CHAT_MESSAGE_ROSHAN_KILL', 'CHAT_MESSAGE_AEGIS_STOLEN',
                        'CHAT_MESSAGE_AEGIS', 'CHAT_MESSAGE_DENIED_AEGIS', 'CHAT_MESSAGE_MINIBOSS_KILL']
    # miniboss is tormentor
    for objective in known_objectives:
        df[objective] = df.get(objective, 0)
    return df


def get_and_score_func():
    # https://overwolf.github.io/api/media/replays/auto-highlights
    # improvement - record the score metrics to a file, check if they have changed, if not, no need to recalculate
    #   also leave in the manual option to manually recalculate the scores
    df = get_df_of_games_that_need_scored()
    if df.empty:
        return
    df = clean_df_and_fill_nas(df)
    df['best_of'] = df['series_type'].map({0: 1, 1: 3, 2: 5})
    df_watched = pd.read_csv(ALREADY_WATCHED_FILE, header=0)
    df_watched['last_watched_on'] = df_watched['last_watched_on'].fillna(datetime.today())
    df_watched['times_watched'] = df_watched['times_watched'].fillna(1)
    df_watched.to_csv(ALREADY_WATCHED_FILE, index=False, header=True)
    df['watched'] = df['match_id'].isin(df_watched['match_id'])
    df['total_kills'] = df['radiant_score'] + df['dire_score']
    df['duration_min'] = (df['duration'] / 60).round()
    df['kills_per_min'] = df['total_kills'] / df['duration_min']
    df = df.rename(columns={"name": "tournament"})
    df = get_team_names_and_ranks(df)
    df = calc_time_ago(df)
    df = calc_game_num(df)
    df = create_title(df)
    df['days_ago'] = (df['date'] - datetime.now()).dt.days
    df = linear_map(df, 'days_ago', f'days_ago_score', -100, 0, 0, 1)
    df[['gold_adv_rate', 'radiant_gold_adv_std', 'swing', 'fight_%_of_game', 'lead_is_small']] = None

    for i, row in df.iterrows():
        # radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        teamfights = df.loc[i, 'teamfights']
        df = add_total_objectives_cols(df, i)
        if teamfights is None:
            df.loc[i, 'first_fight_at'] = 10000
            df.loc[i, 'fight_%_of_game'] = 0
        else:
            df = calc_teamfight_stats(df, i)
        radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        # if np.na or (None or [])
        if (type(radiant_gold_adv) != list and pd.isna(radiant_gold_adv)) or (not radiant_gold_adv):
            df.loc[i, 'radiant_gold_adv_std'] = np.nan
            df.loc[i, 'gold_adv_rate'] = 100
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
            df = calc_gold_adv_rate(df, i, radiant_gold_adv)
            df = calc_gold_adv_std(df, i, radiant_gold_adv)
            df = calc_min_in_lead(df, i, radiant_gold_adv)
            df = calc_max_gold_swing(df, i, radiant_gold_adv)
            df = calc_gold_lead_is_small(df, i, radiant_gold_adv)
    df['swing'] = df['swing'].astype(int)
    df['lead_is_small'] = df['lead_is_small'].astype(float)

    # Number of minutes winning team had a gold advantage near end of game
    col = 'min_in_lead'
    df = linear_map(df, col, f'{col}_score', 0, 10, 1, 0)
    df.loc[df[col] > 10, f'{col}_score'] = 0
    df.loc[df[col] < 5, f'{col}_score'] = 1

    col = 'duration_min'
    df = linear_map(df, col, f'{col}_score', 45, 65, 0, 1)
    df.loc[df[col] < 45, f'{col}_score'] = 0
    df.loc[df[col] > 65, f'{col}_score'] = 1

    col = 'kills_per_min'
    df = linear_map(df, col, f'{col}_score', 0.5, 2, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0
    df.loc[df[col] > 2, f'{col}_score'] = 1

    col = 'lead_is_small'
    df.loc[df[col] == 1, col] = 0
    df = linear_map(df, col, f'{col}_score', 0.5, 1, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0

    col = 'swing'
    df = linear_map(df, col, f'{col}_score', 7000, 12000, 0, 1)
    df.loc[df[col] < 7000, f'{col}_score'] = 0
    df.loc[df[col] > 12000, f'{col}_score'] = 1

    df['good_team_playing_score'] = 0
    df.loc[df["title"].str.contains('|'.join(TEAMS_I_LIKE, ), case=False), f'good_team_playing_score'] = 1

    df['win_team_barracks_lost'] = 63 - np.where(df['radiant_win'] == True, df['barracks_status_radiant'],
                                                 df['barracks_status_dire'])
    df['win_team_barracks_dif'] = np.where(df['radiant_win'] == True,
                                           df['barracks_status_radiant'] - df['barracks_status_dire'],
                                           df['barracks_status_dire'] - df['barracks_status_radiant'])
    score_col = 'barracks_comeback_score'
    df = linear_map(df, 'win_team_barracks_dif', score_col, -36, 63, 0.8, 0)
    df.loc[df['win_team_barracks_dif'] < -36, score_col] = 1
    df.loc[df['win_team_barracks_lost'] == 63, score_col] = 1  # megacreeps comeback

    df['boring'] = (df['lead_is_small'] < 0.7) & (df['swing'] < 5000)
    # df = df[~df['boring']]
    # Game is interesting if it is over 63 minutes, it is close, there is a comeback
    # Do OR operation of these
    df['interesting_score'] = df[['lead_is_small_score', 'min_in_lead_score', 'duration_min_score', 'swing_score',
                                  'barracks_comeback_score']].max(axis=1)
    # increase weight of interestingness score
    weights = {c: 1 for c in HIGHLIGHTS_SCORE_COLS}
    weights['interesting_score'] = 2
    df[HIGHLIGHTS_SCORE_COLS] = df[HIGHLIGHTS_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
    df['highlights_score'] = df[HIGHLIGHTS_SCORE_COLS].mul(pd.Series(weights)).sum(axis=1)
    df[HIGHLIGHTS_SCORE_COLS] = df[HIGHLIGHTS_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
    df['highlights_score'] = df[HIGHLIGHTS_SCORE_COLS].sum(axis=1)
    df['highlights_score'] = df['highlights_score'].astype('float')
    df['highlights_score'] = (df['highlights_score'] / len(HIGHLIGHTS_SCORE_COLS) * 100).round(0)
    df[WHOLE_GAME_SCORE_COLS] = df[WHOLE_GAME_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
    df['whole_game_score'] = df[WHOLE_GAME_SCORE_COLS].max(axis=1).round(2)
    mask = (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1)
    if mask.any():
        df.loc[
            (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1), ['highlights_score']] = \
            df[['highlights_score']] / 2
    df = df.sort_values('highlights_score', ascending=False)
    df_scores = df[['title', 'time_ago', 'highlights_score', 'watched', 'tournament']]
    df.to_csv(SCORES_ALL_COLS_CSV_FILE, header=True, index=False)
    df_scores.to_csv(SCORES_CSV_FILE, header=True, index=False)
    print(df_scores.head(50).to_string())
