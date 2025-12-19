# https://overwolf.github.io/api/media/replays/auto-highlights
from datetime import datetime
from logging import getLogger

import pandas as pd

# from constants import SCORES_CSV_FILE, ALREADY_WATCHED_FILE, SCORES_ALL_COLS_CSV_FILE, \
#     FINAL_SCORE_COLS, \
#     HISTORIC_FILE, REDO_HISTORIC_SCORES, WHOLE_GAME_SCORE_COLS, LATEST_HISTORIC_FILE, SCORES_COLS, \
#     SCORES_ALL_COLS_FOR_EXCEL_CSV_FILE
from constants import FINAL_SCORE_COLS, WHOLE_GAME_SCORE_COLS, SCORES_COLS
from dota.calcs import calculate_all_game_statistics
from dota.calculate_scores import calculate_scores

logger = getLogger(__name__)


# def get_df_of_games_that_need_scored():
#     if REDO_HISTORIC_SCORES:
#         df_raw = pd.read_csv(HISTORIC_FILE)
#         logger.info("recalculating all historic scores")
#         df = df_raw
#     else:
#         df = pd.read_csv(LATEST_HISTORIC_FILE)
#         logger.info("calculating scores for games in past 6 months")
#     return df


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
    df['best_of'] = df['series_type'].map({0: 1, 1: 3, 2: 5})
    return df


def get_and_score_func(df=None):
    # https://overwolf.github.io/api/media/replays/auto-highlights
    # improvement - record the score metrics to a file, check if they have changed, if not, no need to recalculate
    #   also leave in the manual option to manually recalculate the scores
    if df is None:
        df = get_df_of_games_that_need_scored()
    if df.empty:
        return
    df = clean_df_and_fill_nas(df)
    df_watched = pd.read_csv(ALREADY_WATCHED_FILE, header=0)
    df_watched['last_watched_on'] = df_watched['last_watched_on'].fillna(datetime.today())
    df_watched['times_watched'] = df_watched['times_watched'].fillna(1)
    df_watched.to_csv(ALREADY_WATCHED_FILE, index=False, header=True)
    df['watched'] = df['match_id'].isin(df_watched['match_id'])
    df = calculate_all_game_statistics(df)
    df = calculate_scores(df)
    # Game is interesting if it is over 63 minutes, it is close, there is a comeback
    # Do OR operation of these
    df['interesting_score'] = df[['lead_is_small_score', 'min_in_lead_score', 'swing_score',
                                  'barracks_comeback_score']].max(axis=1)
    # increase weight of interestingness score
    weights = {c: 1 for c in FINAL_SCORE_COLS}
    weights['interesting_score'] = 3
    weights['aegis_steals_score'] = 0.1
    df[FINAL_SCORE_COLS] = df[FINAL_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
    df['final_score_total'] = df[FINAL_SCORE_COLS].mul(pd.Series(weights)).sum(axis=1)
    df['final_score_total'] = df['final_score_total'].astype('float')
    df['final_score'] = (df['final_score_total'] / sum(weights.values()) * 100).round(0)
    df[WHOLE_GAME_SCORE_COLS] = df[WHOLE_GAME_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
    df['whole_game_score'] = df[WHOLE_GAME_SCORE_COLS].max(axis=1).round(2)
    mask = (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1)
    if mask.any():
        df.loc[
            (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1), ['final_score']] = \
            df[['final_score']] / 2
    df = df.sort_values('final_score', ascending=False)
    # move useless columns to start of dataframe
    first_columns = ['leagueid', 'match_seq_num', 'start_time', 'duration', 'cluster', 'first_blood_time', 'lobby_type',
                     'human_players', 'positive_votes', 'negative_votes', 'game_mode', 'engine', 'picks_bans',
                     'radiant_team_id', 'dire_team_id', 'radiant_team_complete', 'dire_team_complete',
                     'radiant_captain', 'dire_captain', 'chat', 'version', 'draft_timings',
                     'series_id', 'series_type', 'replay_salt', 'ticket', 'banner', 'tier',
                     'cosmetics', 'radiant_score', 'dire_score', 'radiant_team_name',
                     'dire_team_name', 'radiant_win', 'match_id', 'objectives',
                     'tower_status_radiant', 'tower_status_dire',
                     'barracks_status_radiant', 'barracks_status_dire',
                     'radiant_gold_adv', 'radiant_xp_adv', 'teamfights']
    df = df[first_columns + [c for c in df.columns if c not in first_columns]]
    df_scores = df[SCORES_COLS]
    df.to_csv(SCORES_ALL_COLS_CSV_FILE, header=True, index=False)
    df.head(100).to_csv(SCORES_ALL_COLS_FOR_EXCEL_CSV_FILE, header=True, index=False)
    df_scores.head(100).to_csv(SCORES_CSV_FILE, header=True, index=False)
    return df
