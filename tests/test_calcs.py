import pandas as pd

import dota.calcs as calcs


def test_calculate_all_game_statistics_keeps_first_fight_at_string(monkeypatch):
    def fake_get_team_names_and_ranks(df, df_teams=None):
        return df.assign(
            radiant_team_name="Radiant",
            dire_team_name="Dire",
            radiant_team_rank=1,
            dire_team_rank=2,
        )

    monkeypatch.setattr(calcs, "get_team_names_and_ranks", fake_get_team_names_and_ranks)

    df = pd.DataFrame(
        [
            {
                "radiant_score": 20,
                "dire_score": 18,
                "duration": 2400,
                "name": "Test Tournament",
                "radiant_team_id": 1,
                "dire_team_id": 2,
                "start_time": 1700000000,
                "series_id": 100,
                "teamfights": None,
                "objectives": [],
                "radiant_gold_adv": None,
                "radiant_win": True,
            }
        ]
    )

    out = calcs.calculate_all_game_statistics(df)
    assert isinstance(out.loc[0, "first_fight_at"], str)
    assert out.loc[0, "first_fight_at"] == "10000"
