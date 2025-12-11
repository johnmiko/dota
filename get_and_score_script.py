# https://overwolf.github.io/api/media/replays/auto-highlights
import ast
import datetime
import json
from datetime import datetime as dt2

import numpy as np
import pandas as pd
import requests

from calcs import calc_teamfight_stats, calc_gold_adv_rate, calc_gold_adv_std, calc_min_in_lead, \
    calc_max_gold_swing, calc_game_is_close, get_team_names, calc_time_ago, create_title, calc_game_num
from constants import RAW_FILE, SCORES_CSV_FILE, ALREADY_WATCHED_FILE, SCORES_ALL_COLS_CSV_FILE, DATE_STR_FORMAT, \
    HIGHLIGHTS_SCORE_COLS
from score import linear_map


# def get_interesting_games():
def get_more_data():
    pass


update_data = True
if update_data:
    pass
limit = 1000
url = f"""https://api.opendota.com/api/explorer?sql=SELECT * 
FROM matches
JOIN leagues using(leagueid)
WHERE name not like '%Division II%'
ORDER BY matches.start_time DESC
LIMIT {limit}"""
r = requests.get(url, timeout=45)
if r.status_code != 200:
    print(r.text)
matches = r.json()['rows']
df_new = pd.DataFrame(matches)
df_raw = pd.read_csv(RAW_FILE)
df = pd.concat([df_new, df_raw])
df = df.drop_duplicates('match_id')
df.to_csv(RAW_FILE, index=False, header=True)
df['start_time'] = df['start_time'].fillna(0)
df['date'] = pd.to_datetime(df['start_time'], unit='s')
df['name'] = df['name'].fillna('')
df = df[~df['name'].str.contains('Division II')]
df_watched = pd.read_csv(ALREADY_WATCHED_FILE, header=0)
df_watched['last_watched_on'] = df_watched['last_watched_on'].fillna(datetime.datetime.today())
df_watched['times_watched'] = df_watched['times_watched'].fillna(1)
df_watched.to_csv(ALREADY_WATCHED_FILE, index=False, header=True)
df['watched'] = df['match_id'].isin(df_watched['match_id'])
df['total_kills'] = df['radiant_score'] + df['dire_score']
df['duration_min'] = (df['duration'] / 60).round()
df['kills_per_min'] = df['total_kills'] / df['duration_min']
df = get_team_names(df)
df = calc_time_ago(df)
df = calc_game_num(df)
df = create_title(df)
df[['gold_adv_rate', 'radiant_gold_adv_std', 'swing', 'fight_%_of_game', 'lead_is_small']] = None

for i, row in df.iterrows():
    # radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
    teamfights = df.loc[i, 'teamfights']
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
        df = calc_game_is_close(df, i, radiant_gold_adv)
df['swing'] = df['swing'].astype(int)
df['lead_is_small'] = df['lead_is_small'].astype(float)

col = 'min_in_lead'
df = linear_map(df, col, f'{col}_score', 5, 10, 1, 0)
df.loc[df[col] > 10, f'{col}_score'] = 0
df.loc[df[col] < 5, f'{col}_score'] = 1

col = 'duration_min'
df = linear_map(df, col, f'{col}_score', 45, 63, 0, 1)
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
df = linear_map(df, col, f'{col}_score', 5000, 13000, 0, 1)
df.loc[df[col] < 7000, f'{col}_score'] = 0
df.loc[df[col] > 12000, f'{col}_score'] = 1

col = 'date'
df[f'{col}_score'] = 0
# 7.33 patch date
df.loc[df[col] > dt2(2023, 4, 19),] = 1
# inverse the days so we can scale it from 0-1


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


df['highlights_score'] = df[HIGHLIGHTS_SCORE_COLS].sum(axis=1)
df['highlights_score'] = (df['highlights_score'] / len(HIGHLIGHTS_SCORE_COLS) * 100).round(0)
# Not using whole game score right now
# df['whole_game_score'] = df[whole_game_score].max(axis=1).round(2)
mask = (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1)
if mask.any():
    df.loc[
        (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1), ['highlights_score']] = \
        df[['highlights_score']] / 2
df = df.sort_values('highlights_score', ascending=False)
df_scores = df[['title', 'time_ago', 'highlights_score', 'watched']]
df.to_csv(SCORES_ALL_COLS_CSV_FILE, header=True, index=False)
df_scores.to_csv(SCORES_CSV_FILE, header=True, index=False)
print(df_scores.head(50).to_string())

from datetime import datetime

filename = 'text/temp.csv'
with open(filename, 'a+') as f:
    f.write(datetime.utcnow().strftime(DATE_STR_FORMAT) + '\n')
with open(filename, 'r') as f:
    text = f.readlines()
print('temp.csv content')
print(text)
