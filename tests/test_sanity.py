# def test_sanity():
import pandas as pd

from constants import HISTORIC_FILE

df_manual_scores = pd.read_csv("games_that_were_interesting.txt")
df_historic = pd.read_csv(HISTORIC_FILE)
df_to_recalculate = df_historic[df_historic['match_id'].isin(df_manual_scores['match_id'])]
df_to_recalculate = df_historic.merge(
    df_manual_scores[["match_id", "my_score"]],
    on="match_id",
    how="inner"
)
df_scored = get_and_score_func(df_to_recalculate)
