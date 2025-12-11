from logging import getLogger

import pandas as pd

from constants import SCORES_ALL_COLS_CSV_FILE, HIGHLIGHT_VIDEOS, SCORES_NO_HIGHLIGHTS

logger = getLogger(__name__)


def find_games_without_highlights():
    logger.info('finding games that do not have highlights')
    df_scores = pd.read_csv(SCORES_ALL_COLS_CSV_FILE)
    df_scores = df_scores[df_scores['watched'] == False]
    teams_have_names_mask = ~(df_scores['radiant_team_name'] == '???') | (df_scores['dire_team_name'] == '???')
    df_scores = df_scores[teams_have_names_mask]
    df_scores = df_scores.head(500)
    team_name_cols = ['radiant_team_name', 'dire_team_name']
    # check if both team names are in title
    df_scores['start_time_date'] = pd.to_datetime(df_scores['start_time'], unit='s').dt.tz_localize('UTC')
    # Need to match by name and by date
    # K baby steps, match the names
    df_highlights = pd.read_csv(HIGHLIGHT_VIDEOS)
    df_highlights['title'] = df_highlights['title'].str.lower()
    df_highlights['publishTime_date'] = pd.to_datetime(df_highlights['publishTime'])
    df_scores['radiant_team_name'] = df_scores['radiant_team_name'].str.lower()
    df_scores['dire_team_name'] = df_scores['dire_team_name'].str.lower()
    df_scores['has_highlights'] = False
    df_scores['url'] = ''
    # Find the overlap of name matches
    # df = pd.DataFrame()
    # df['C'] = df.apply(lambda x: x.A in x.B, axis=1)
    # df_scores["name_match"] = df_scores.apply(lambda row: rowA in x.B, axis=1)
    # df_scores["name_match"] = (df_scores['radiant_team_name'] in row2['title']) and (
    #             row1['dire_team_name'] in row2['title'])
    for i1, row1 in df_scores.iterrows():
        for i2, row2 in df_highlights.iterrows():
            name_match = (row1['radiant_team_name'] in row2['title']) and (row1['dire_team_name'] in row2['title'])
            if name_match:
                delta = row1['start_time_date'] - row2['publishTime_date']
                if delta.days < 2:
                    df_scores.at[i1, 'has_highlights'] = True
    ##### chat attempt #####
    # df_scores['start_time_date'] = pd.to_datetime(df_scores['start_time_date'])
    # df_highlights['publishTime_date'] = pd.to_datetime(df_highlights['publishTime_date'])
    #
    # # Create a list to store the indices of matching rows in df_scores
    # matching_indices = []
    #
    # # Iterate through each row in df_scores
    # for i, row in df_scores.iterrows():
    #     # Check if both radiant_team_name and dire_team_name are present in any title in df_highlights
    #     name_match = df_highlights['title'].str.contains(row['radiant_team_name']) & df_highlights['title'].str.contains(row['dire_team_name'])
    #     # Filter the rows in df_highlights where name_match is True and the time delta is less than 2 days
    #     filtered_highlights = df_highlights[
    #         name_match & (df_highlights['publishTime_date'] - row['start_time_date']).dt.days < 2]
    #     # If there are any matching rows in df_highlights, set 'has_highlights' to True for the current row in df_scores
    #     if not filtered_highlights.empty:
    #         matching_indices.append(i)

    # Update the 'has_highlights' column in df_scores based on the matching indices
    # df_scores.loc[matching_indices, 'has_highlights'] = True
    ##### chat attempt #####
    df_no_highlights = df_scores[df_scores['has_highlights'] == False]
    # df_no_highlights['url'] = 'https://www.youtube.com/watch?v=' + df_scores['video_id']
    df_no_highlights = df_no_highlights[['match_id', 'title', 'time_ago', 'highlights_score', 'watched']]
    df_no_highlights.to_csv(SCORES_NO_HIGHLIGHTS, index=False)
    return df_no_highlights
