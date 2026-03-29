import datetime as dt

import pandas as pd
from fastapi.testclient import TestClient

import app as app_mod
from database import SessionLocal, CachedMatch

client = TestClient(app_mod.app)


def test_api_matches_happy_path(monkeypatch):
    """Calls /api/matches with mocked data and verifies response shape."""
    now = dt.datetime.now()
    df = pd.DataFrame([
        {
            "match_id": 123456,
            "title": "Radiant vs Dire",
            "days_ago": 0.5,
            "date": now - dt.timedelta(hours=12),
            # Inputs used to compute 'interesting_score'
            "lead_is_small_score": 0.9,
            "min_in_lead_score": 0.8,
            "swing_score": 0.7,
            "barracks_comeback_score": 0.0,
            # Final and whole-game score components
            "days_ago_score": 0.9,
            "good_team_playing_score": 0.5,
            "aegis_steals_score": 0.0,
            "fight_%_of_game_score": 0.6,
            # Display fields
            "radiant_team_name": "Radiant",
            "dire_team_name": "Dire",
            "duration_min": 45,
            "first_fight_at": "00:05",
            "tournament": "Test Cup",
            "start_time": int(now.timestamp()),
        }
    ])

    # Patch heavy functions to make the pipeline a pass-through
    monkeypatch.setattr(app_mod, "fetch_dota_data_from_api", lambda: df)
    monkeypatch.setattr(app_mod, "clean_df_and_fill_nas", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_all_game_statistics", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_statistics_scores", lambda d: d)
    monkeypatch.setattr(
        app_mod,
        "calculate_subjective_weighted_scores",
        lambda d: d.assign(final_score=88.8, days_ago_pretty="12 hours ago"),
    )

    resp = client.get("/api/matches")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1

    item = data[0]
    # Persisted match_id is stored as string in the DB model
    assert item["match_id"] == "123456"
    assert item["title"] == "Radiant vs Dire"
    # Endpoint computes pretty time and final score
    assert item["days_ago_pretty"] is not None
    assert item["final_score"] is not None
    # Optional fields should be present
    assert item["radiant_team_name"] == "Radiant"
    assert item["dire_team_name"] == "Dire"
    assert item["duration_min"] == 45

def test_api_matches_cached_populates_cache(monkeypatch):
    """Calls /api/matches_cached and verifies cache table upsert behavior."""
    now = dt.datetime.now()
    df = pd.DataFrame([
        {
            "match_id": 222222,
            "title": "Game A",
            "days_ago": -1.0,
            "date": now - dt.timedelta(days=1),
            "lead_is_small_score": 0.3,
            "min_in_lead_score": 0.2,
            "swing_score": 0.4,
            "barracks_comeback_score": 0.0,
            "days_ago_score": 0.5,
            "good_team_playing_score": 0.5,
            "aegis_steals_score": 0.0,
            "fight_%_of_game_score": 0.3,
            "radiant_team_name": "R1",
            "dire_team_name": "D1",
            "duration_min": 40,
            "first_fight_at": "00:06",
            "tournament": "Edge Cup",
        },
        {
            "match_id": 333333,
            "title": "??? redacted title",  # skipped by cache refresh logic
            "days_ago": -1.0,
            "date": now - dt.timedelta(days=1),
            "lead_is_small_score": 0.6,
            "min_in_lead_score": 0.7,
            "swing_score": 0.6,
            "barracks_comeback_score": 0.0,
            "days_ago_score": 0.5,
            "good_team_playing_score": 0.5,
            "aegis_steals_score": 0.0,
            "fight_%_of_game_score": 0.6,
            "radiant_team_name": "R1",
            "dire_team_name": "D1",
            "duration_min": 40,
            "first_fight_at": "00:06",
            "tournament": "Edge Cup",
        },
    ])

    monkeypatch.setattr(app_mod, "fetch_dota_data_from_api", lambda: df)
    monkeypatch.setattr(app_mod, "clean_df_and_fill_nas", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_all_game_statistics", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_statistics_scores", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_subjective_weighted_scores", lambda d: d.assign(final_score=75.0))

    resp = client.get("/api/matches_cached?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["match_id"] == "222222"

    s = SessionLocal()
    try:
        rows = s.query(CachedMatch).all()
        assert len(rows) == 1
        assert rows[0].match_id == "222222"
    finally:
        s.close()
