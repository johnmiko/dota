import datetime as dt

import pandas as pd

import app as app_mod
from database import SessionLocal, CachedMatch


def test_refresh_cached_matches_upserts_and_prunes(monkeypatch):
    now = dt.datetime.now()
    df = pd.DataFrame(
        [
            {
                "match_id": 123,
                "title": "Good Match",
                "days_ago": -1.0,
                "date": now - dt.timedelta(days=1),
                "final_score": 77.5,
                "radiant_team_name": "Team A",
                "dire_team_name": "Team B",
                "duration_min": 42,
                "tournament": "Cup",
            },
            {
                "match_id": 124,
                "title": "Too Old",
                "days_ago": -200.0,
                "date": now - dt.timedelta(days=200),
                "final_score": 10.0,
                "radiant_team_name": "Team C",
                "dire_team_name": "Team D",
                "duration_min": 30,
                "tournament": "Old Cup",
            },
            {
                "match_id": 125,
                "title": "??? hidden",
                "days_ago": -2.0,
                "date": now - dt.timedelta(days=2),
                "final_score": 50.0,
                "radiant_team_name": "Team E",
                "dire_team_name": "Team F",
                "duration_min": 33,
                "tournament": "Cup",
            },
        ]
    )

    monkeypatch.setattr(app_mod, "fetch_dota_data_from_api", lambda: df)
    monkeypatch.setattr(app_mod, "clean_df_and_fill_nas", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_all_game_statistics", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_statistics_scores", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_subjective_weighted_scores", lambda d: d)

    inserted = app_mod._refresh_cached_matches(days_limit=100)
    assert inserted == 1

    s = SessionLocal()
    try:
        rows = s.query(CachedMatch).all()
        assert len(rows) == 1
        assert rows[0].match_id == "123"
        assert rows[0].title == "Good Match"
    finally:
        s.close()
