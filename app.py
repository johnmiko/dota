from typing import List, Dict, Any
import os
import requests

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from constants import SCORES_COLS, FINAL_SCORE_COLS, WHOLE_GAME_SCORE_COLS
from dota.get_and_score_func import clean_df_and_fill_nas, calculate_all_game_statistics, calculate_scores

PLAYER_ID = os.getenv("PLAYER_ID", "123456789")  # Set your OpenDota player ID here

app = FastAPI(title="Dota Game Finder API")

ratings = {}  # In-memory storage for user ratings; won't persist across restarts

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RateMatchRequest(BaseModel):
    match_id: int
    title: str = ""
    score: int

@app.get("/", response_class=HTMLResponse)
async def index():
    # For now, return a simple HTML response since templates might not be set up
    return """
    <html>
        <head><title>Dota Game Finder</title></head>
        <body>
            <h1>Dota Game Finder API</h1>
            <p>API endpoints available at /api/matches, /api/recalculate, /api/rate_match</p>
        </body>
    </html>
    """

@app.get("/api/matches")
async def get_matches() -> List[Dict[str, Any]]:
    try:
        # Fetch recent matches from OpenDota API
        response = requests.get(f"https://api.opendota.com/api/players/{PLAYER_ID}/matches?limit=100")
        response.raise_for_status()
        matches_data = response.json()

        if not matches_data:
            return []

        # Convert to DataFrame
        df = pd.DataFrame(matches_data)

        # Clean and fill NAs
        df = clean_df_and_fill_nas(df)

        # Skip watched for now, or add logic if needed
        # For simplicity, assume all are unwatched
        df['watched'] = False

        # Calculate statistics and scores
        df = calculate_all_game_statistics(df)
        df = calculate_scores(df)

        # Calculate interesting_score and final_score as in original
        df['interesting_score'] = df[['lead_is_small_score', 'min_in_lead_score', 'swing_score',
                                      'barracks_comeback_score']].max(axis=1)
        weights = {c: 1 for c in FINAL_SCORE_COLS}
        weights['interesting_score'] = 3
        weights['aegis_steals_score'] = 0.1
        df[FINAL_SCORE_COLS] = df[FINAL_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
        df['final_score_total'] = df[FINAL_SCORE_COLS].mul(pd.Series(weights)).sum(axis=1)
        df['final_score_total'] = df['final_score_total'].astype('float')
        df['final_score'] = (df['final_score_total'] / sum(weights.values()) * 100).round(0)
        df[WHOLE_GAME_SCORE_COLS] = df[WHOLE_GAME_SCORE_COLS].apply(pd.to_numeric, errors='coerce')
        df['whole_game_score'] = df[WHOLE_GAME_SCORE_COLS].max(axis=1).round(2)
        mask = (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1)
        if mask.any():
            df.loc[(df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1), ['final_score']] = \
                df[['final_score']] / 2
        df = df.sort_values('final_score', ascending=False)

        # Add user ratings if available
        df['user_score'] = df['match_id'].map(lambda mid: ratings.get(str(mid), {}).get('score', None))
        df['user_title'] = df['match_id'].map(lambda mid: ratings.get(str(mid), {}).get('title', ''))

        # Select columns
        df_scores = df[SCORES_COLS + ['user_score', 'user_title']]

        # Convert to list of dicts
        matches = df_scores.head(100).to_dict('records')
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recalculate")
async def recalculate():
    # This endpoint is kept for backward compatibility but does nothing
    # since we fetch fresh data on each request to /api/matches
    return {"status": "success"}

@app.post("/api/rate_match")
async def rate_match(request: RateMatchRequest):
    try:
        match_id = str(request.match_id)
        title = request.title
        score = request.score

        # Store in in-memory dict
        ratings[match_id] = {'title': title, 'score': score}

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
