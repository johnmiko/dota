import os
import csv
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from constants import SCORES_CSV_FILE, SCORES_COLS, PROJ_DIR
from dota.get_and_score_func import get_and_score_func

app = FastAPI(title="Dota Game Finder API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

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
        # Check if scores file exists, if not generate it
        if not os.path.exists(SCORES_CSV_FILE):
            get_and_score_func()

        # Read and return the scores
        df = pd.read_csv(SCORES_CSV_FILE)
        # Convert to list of dicts for JSON response
        matches = df[SCORES_COLS].to_dict('records')
        return matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recalculate")
async def recalculate():
    try:
        # Trigger recalculation
        get_and_score_func()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rate_match")
async def rate_match(request: RateMatchRequest):
    try:
        match_id = request.match_id
        title = request.title
        score = request.score

        # Path to the interesting games file
        interesting_file = Path(PROJ_DIR) / 'tests' / 'games_that_were_interesting.txt'

        # Check if match already exists
        existing_entries = []
        match_exists = False

        if interesting_file.exists():
            with open(interesting_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('match_id') == str(match_id):
                        row['my_score'] = str(score)
                        if not title and 'title' in row:
                            title = row['title']
                        match_exists = True
                    existing_entries.append(row)

        # Add new entry if it doesn't exist
        if not match_exists:
            existing_entries.append({
                'match_id': str(match_id),
                'title': title,
                'my_score': str(score)
            })

        # Write back to file
        fieldnames = ['match_id', 'title', 'my_score']
        with open(interesting_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(existing_entries)

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
