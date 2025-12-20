import os
import sys
import pathlib
import datetime as dt

# Force local SQLite DB for tests before importing app/database
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_api_matches.db")

# Ensure the project root (containing app.py) is on the path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from fastapi.testclient import TestClient

import app as app_mod
from database import SessionLocal, LatestMatch
import pytest

client = TestClient(app_mod.app)


def test_api_matches_happy_path(monkeypatch):
    """Calls /api/matches with a mocked dataset and verifies persistence & shape."""
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
        }
    ])

    # Patch heavy functions to make the pipeline a pass-through
    monkeypatch.setattr(app_mod, "fetch_dota_data_from_api", lambda: df)
    monkeypatch.setattr(app_mod, "clean_df_and_fill_nas", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_all_game_statistics", lambda d: d)
    monkeypatch.setattr(app_mod, "calculate_statistics_scores", lambda d: d)

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

    # Verify persistence in latest_matches table
    s = SessionLocal()
    try:
        rows = s.query(LatestMatch).all()
        assert len(rows) == 1
        assert rows[0].match_id == "123456"
        assert rows[0].title == "Radiant vs Dire"
    finally:
        s.close()


@pytest.mark.xfail(reason="Duplicate match_id currently triggers unique constraint until dedupe is implemented")
def test_api_matches_duplicate_ids(monkeypatch):
    """Edge-case: two rows with the same match_id should result in a single persisted item."""
    now = dt.datetime.now()
    df = pd.DataFrame([
        {
            "match_id": 222222,
            "title": "Game A",
            "days_ago": 1.0,
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
            "match_id": 222222,
            "title": "Game A (dup)",
            "days_ago": 1.0,
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

    resp = client.get("/api/matches")
    # Desired behavior after dedupe: 200 with one item
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_latest_matches_crud():
    """Direct DB test: create, read, verify, delete a LatestMatch entry."""
    s = SessionLocal()
    try:
        # Add a new entry
        new_match = LatestMatch(
            match_id="test_123",
            title="Test Match for CRUD",
            days_ago=2.5,
            days_ago_pretty="2 days ago",
            final_score=75.5,
            first_fight_at="00:10",
            tournament="Test Tournament",
            radiant_team_name="Test Radiant",
            dire_team_name="Test Dire",
            duration_min=50,
            user_score=8,
            user_title="Great Game"
        )
        s.add(new_match)
        s.commit()

        # Query and verify it was added
        retrieved = s.query(LatestMatch).filter(LatestMatch.match_id == "test_123").first()
        assert retrieved is not None
        assert retrieved.title == "Test Match for CRUD"
        assert retrieved.final_score == 75.5
        assert retrieved.duration_min == 50
        assert retrieved.user_score == 8

        # Delete the entry
        s.delete(retrieved)
        s.commit()

        # Verify it was deleted
        deleted = s.query(LatestMatch).filter(LatestMatch.match_id == "test_123").first()
        assert deleted is None
    finally:
        s.close()
