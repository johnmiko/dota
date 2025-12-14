import json
from datetime import datetime
from logging import getLogger

import pandas as pd
from pandas.errors import EmptyDataError

from constants import DATE_STR_FORMAT, ALREADY_WATCHED_FILE, LAST_RUN_FILE
from ease_of_use import pdf

logger = getLogger(__name__)

print_cols = ['title', 'time_ago']


def create_highlights_df(df, cols):
    cols2 = print_cols
    cols2.extend(cols)
    cols2 = list(set(cols2))
    df = df.sort_values('highlights_score', ascending=False)
    df = df.set_index('match_id')
    return df[cols2]


def print_highlights_df(df, cols, rows=10):
    print()
    cols2 = print_cols
    cols2.extend(cols)
    df = df.sort_values('highlights_score', ascending=False)
    df = df.set_index('match_id')
    print('highlights df')
    pdf(df[cols2].head(rows))
    print()


def create_wholegame_df(df, cols, rows=10):
    cols2 = print_cols
    cols2.extend(cols)
    cols2 = list(set(cols2))
    df = df.sort_values('whole_game_score', ascending=False)
    df = df.set_index('match_id')
    return df[cols2].head(rows)


def print_whole_game_df(df, cols, rows=5):
    print()
    cols2 = print_cols
    cols2.extend(cols)
    print('whole game df')
    df = df.sort_values('whole_game_score', ascending=False)
    df = df.set_index('match_id')
    pdf(df[cols2].head(rows))
    print()


def create_empty_file(filename):
    with open(filename, 'w+'):
        pass


def read_csv_wrapper(filename, **kwargs):
    try:
        df = pd.read_csv(filename, **kwargs)
    except (FileNotFoundError, EmptyDataError):
        create_empty_file(filename)
        df = pd.DataFrame()
    return df


def last_ran(filename):
    with open(filename, 'r') as f:
        last_ran_str = f.read()
    last_ran_date = datetime.strptime(last_ran_str, DATE_STR_FORMAT)
    with open(filename, 'w') as f:
        f.write(datetime.now().strftime(DATE_STR_FORMAT))
    return last_ran_date


# def should_run_based_on_file(last_ran_file, run_every_x_hours):
#     last_ran_date = last_ran(last_ran_file)
#     utc_now = datetime.utcnow()
#     delta = utc_now - last_ran_date
#     delta_seconds = delta.days * 3600 * 24 + delta.seconds
#     delta_hours = round(delta_seconds / 3600, 1)
#     should_run = delta_hours > run_every_x_hours
#     if should_run:
#         status = 'running'
#     else:
#         status = 'skipping'
#     logger.info(f'last ran {delta_hours} hours ago, {status} {last_ran_file}')
#     return should_run


def should_run(last_ran_dict, key, run_every_x_hours):
    # should run based on dict
    try:
        last_ran_date = last_ran_dict[key]
    except KeyError:
        last_ran_dict[key] = datetime.now()
        with open(LAST_RUN_FILE, "w") as f:
            json.dump(last_ran_dict, f)
        logger.info(f'key not found, running {key}')
        return True
    utc_now = datetime.now()
    delta = utc_now - last_ran_date
    delta_seconds = delta.days * 3600 * 24 + delta.seconds
    delta_hours = round(delta_seconds / 3600, 1)
    will_run = delta_hours > run_every_x_hours
    if will_run:
        status = 'running'
    else:
        status = 'skipping'
    logger.info(f'last ran {delta_hours} hours ago, {status} {key}')
    return will_run


def update_df_watched():
    df_watched = pd.read_csv(ALREADY_WATCHED_FILE, header=0)
    df_watched['last_watched_on'] = df_watched['last_watched_on'].fillna(datetime.today())
    df_watched['times_watched'] = df_watched['times_watched'].fillna(1)
    df_watched.to_csv(ALREADY_WATCHED_FILE, index=False, header=True)
