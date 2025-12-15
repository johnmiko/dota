import numpy as np

from dota.score import linear_map


def calculate_scores(df):
    col = 'fight_%_of_game'
    df[col] = df[col].astype(float)
    df = linear_map(df, col, f'{col}_score', 0.05, 0.25, 0, 1)
    df.loc[df[col] > 0.25, f'{col}_score'] = 1
    df.loc[df[col] < 0.05, f'{col}_score'] = 0
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    # Number of minutes winning team had a gold advantage towards end of game
    # Improvement, should be taking into account how long the game is as well. Not as interesting if the game is 20 minutes
    # Should include as a percentage as well
    col = 'min_in_lead'
    df = linear_map(df, col, f'{col}_score', 5, 10, 1, 0)
    df.loc[df[col] > 10, f'{col}_score'] = 0
    df.loc[df[col] < 5, f'{col}_score'] = 1
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    col = 'duration_min'
    df = linear_map(df, col, f'{col}_score', 45, 65, 0, 1)
    df.loc[df[col] < 45, f'{col}_score'] = 0
    df.loc[df[col] > 65, f'{col}_score'] = 1
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    col = 'kills_per_min'
    df = linear_map(df, col, f'{col}_score', 0.5, 2, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0
    df.loc[df[col] > 2, f'{col}_score'] = 1
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    col = 'lead_is_small'
    df.loc[df[col] == 1, col] = 0
    df = linear_map(df, col, f'{col}_score', 0.5, 1, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    col = 'swing'
    df = linear_map(df, col, f'{col}_score', 7000, 12000, 0, 1)
    df.loc[df[col] < 7000, f'{col}_score'] = 0
    df.loc[df[col] > 12000, f'{col}_score'] = 1
    df[f'{col}_score'] = df[f'{col}_score'].round(2)

    # improvement, use objectives to calculate an objectives_score instead, so we can ignore the little buildings in the base
    df['win_team_barracks_lost'] = 63 - np.where(df['radiant_win'] == True, df['barracks_status_radiant'],
                                                 df['barracks_status_dire'])
    df['win_team_barracks_dif'] = np.where(df['radiant_win'] == True,
                                           df['barracks_status_radiant'] - df['barracks_status_dire'],
                                           df['barracks_status_dire'] - df['barracks_status_radiant'])
    score_col = 'barracks_comeback_score'
    df = linear_map(df, 'win_team_barracks_dif', score_col, -36, 63, 0.8, 0)
    df.loc[df['win_team_barracks_dif'] < -36, score_col] = 1
    df.loc[df['win_team_barracks_lost'] == 63, score_col] = 1  # megacreeps comeback
    df[score_col] = df[score_col].round(2)

    df['boring'] = (df['lead_is_small'] < 0.7) & (df['swing'] < 5000)
    # df = df[~df['boring']]
    df["aegis_steals_score"] = 0
    # Add 0.1 to score if there's an aegis steal or deny
    df["aegis_steals_score"] = (df["CHAT_MESSAGE_AEGIS_STOLEN"] + df["CHAT_MESSAGE_DENIED_AEGIS"] > 0).astype(float)

    # df['good_team_playing_score'] = 0
    # df.loc[df["title"].str.contains('|'.join(TEAMS_I_LIKE, ), case=False), f'good_team_playing_score'] = 1
    # If 2 top tier teams are playing score=1
    # If 2 good teams are playing score=0.75
    # If 1 top tier is playing score=0.75
    # If 1 good team playing score=0.5
    # if no good teams score=0
    # Aurora gaming at 13 currently
    mx = df[["radiant_team_rank", "dire_team_rank"]].max(axis=1)
    mn = df[["radiant_team_rank", "dire_team_rank"]].min(axis=1)
    df["good_team_playing_score"] = np.select(
        [mx < 6, mx < 14, mn < 6, mn < 14],
        [1.0, 0.75, 0.75, 0.5],
        default=0.0
    )
    df["good_team_playing_score"] = df["good_team_playing_score"].round(2)
    return df
