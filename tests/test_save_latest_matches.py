"""
Test script for _save_to_latest_matches function.
Run this manually to test saving matches to the latest_matches table.

Usage:
    pytest tests/test_save_latest_matches.py -v
"""

import os
import sys
import pathlib

# Force local SQLite DB for tests before importing app/database
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_save_latest_matches.db")

# Ensure the project root (containing app.py) is on the path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from database import SessionLocal, LatestMatch, MatchRating
from app import _save_to_latest_matches


def test_save_to_latest_matches():
    """Test saving matches to the latest_matches table."""
    
    # Create sample data similar to what the API would return
    sample_data = {
        'match_id': [123456789, 987654321, 555666777],
        'title': ['Epic Comeback Game', 'Team Secret vs OG', 'Fast-paced Thriller'],
        'days_ago': [1.5, 3.2, 0.8],
        'days_ago_pretty': ['1 day ago', '3 days ago', '19 hours ago'],
        'final_score': [85.5, 92.3, 78.1],
        'first_fight_at': ['5:30', '3:45', '2:15'],
        'tournament': ['DPC WEU', 'ESL One', 'DPC WEU'],
        'radiant_team_name': ['Team Secret', 'OG', 'Liquid'],
        'dire_team_name': ['Tundra', 'Team Secret', 'Alliance'],
        'duration_min': [45, 52, 38],
    }
    
    df = pd.DataFrame(sample_data)

    # Create a database session
    db = SessionLocal()    
    
    try:
        # Clear any existing test data
        db.query(LatestMatch).delete()
        db.query(MatchRating).delete()
        db.commit()
        
        # Create some sample user ratings
        print("\n" + "="*60)
        print("Setting up sample user ratings...")
        rated_matches = {}
        
        # Add a rating for the first match
        rating = MatchRating(
            match_id=str(sample_data['match_id'][0]),
            title=sample_data['title'][0],
            score=90
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        rated_matches[str(sample_data['match_id'][0])] = rating
        
        print(f"Sample ratings created: {len(rated_matches)} ratings")
        
        # Call the function under test
        print("\nCalling _save_to_latest_matches...")
        count = _save_to_latest_matches(df, db, rated_matches)
        print(f"✅ Successfully saved {count} matches to latest_matches table")
        
        assert count == 3, f"Expected 3 matches saved, got {count}"
        
        # Verify the results
        print("\nVerifying saved data...")
        for match_id in sample_data['match_id']:
            saved_match = db.query(LatestMatch).filter(
                LatestMatch.match_id == str(match_id)
            ).first()
            
            assert saved_match is not None, f"Match {match_id} not found in database"
            
            print(f"\n✅ Match {match_id} found in database:")
            print(f"   Title: {saved_match.title}")
            print(f"   Final Score: {saved_match.final_score}")
            print(f"   Days Ago: {saved_match.days_ago}")
            print(f"   Days Ago Pretty: {saved_match.days_ago_pretty}")
            print(f"   Tournament: {saved_match.tournament}")
            print(f"   Teams: {saved_match.radiant_team_name} vs {saved_match.dire_team_name}")
            print(f"   Duration: {saved_match.duration_min} min")
            print(f"   User Score: {saved_match.user_score}")
            print(f"   User Title: {saved_match.user_title}")
        
        # Verify first match has user rating
        first_match = db.query(LatestMatch).filter(
            LatestMatch.match_id == str(sample_data['match_id'][0])
        ).first()
        assert first_match.user_score == 90, f"Expected user_score 90, got {first_match.user_score}"
        print(f"\n✅ User rating correctly associated with match")
        
        # Test update functionality - run the same function again
        print("\n" + "="*60)
        print("Testing update functionality (running again with modified data)...")
        df.loc[0, 'final_score'] = 95.0  # Change the score
        df.loc[0, 'title'] = 'Updated Epic Comeback Game'
        
        count = _save_to_latest_matches(df, db, rated_matches)
        print(f"✅ Successfully updated {count} matches")
        
        # Verify the update
        updated_match = db.query(LatestMatch).filter(
            LatestMatch.match_id == str(sample_data['match_id'][0])
        ).first()
        
        assert updated_match.final_score == 95.0, f"Expected updated score 95.0, got {updated_match.final_score}"
        assert updated_match.title == 'Updated Epic Comeback Game', f"Title not updated correctly"
        
        print(f"✅ Match score successfully updated to {updated_match.final_score}")
        print(f"✅ Match title successfully updated to '{updated_match.title}'")
        
        # Count total matches in latest_matches table
        total_count = db.query(LatestMatch).count()
        print(f"\n📊 Total matches in latest_matches table: {total_count}")
        assert total_count == 3, f"Expected 3 total matches, got {total_count}"
        
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60 + "\n")
        
    finally:
        # Cleanup
        db.query(LatestMatch).delete()
        db.query(MatchRating).delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_save_to_latest_matches()
