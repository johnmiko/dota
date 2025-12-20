import os
from typing import List, Dict, Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from constants import SCORES_COLS, FINAL_SCORE_COLS, WHOLE_GAME_SCORE_COLS
from datetime import datetime
from database import SessionLocal, MatchRating, CachedMatch, LatestMatch, init_db, get_db, engine
from dota.api import fetch_dota_data_from_api
from dota.get_and_score_func import clean_df_and_fill_nas, calculate_all_game_statistics, calculate_scores

# Initialize database tables
init_db()

app = FastAPI(title="Dota Game Finder API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Explicit production domain
    allow_origins=[
        "https://portfoliovercel-lime.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    # Allow preview deployments for this project on vercel.app
    allow_origin_regex=r"^https://portfoliovercel-.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RateMatchRequest(BaseModel):
    match_id: int
    score: int


@app.get("/", response_class=HTMLResponse)
async def index():
    # For now, return a simple HTML response since templates might not be set up
    return """
    <html>
        <head><title>Dota Game Finder</title></head>
        <body>
            <h1>Dota Game Finder API</h1>
            <p>API endpoints available at /api/matches, /api/matches_cached, /api/recalculate, /api/rate_match, /api/health</p>
        </body>
    </html>
    """


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API and database are running."""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    # Masked DB URL for verification (no password)
    masked_db_url = None
    try:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            masked_db_url = _mask_url(db_url)
    except Exception:
        masked_db_url = None

    return {
        "status": "healthy",
        "database": db_status,
        "db_url": masked_db_url,
    }

def _mask_url(url: str) -> str:
    try:
        if "@" in url and "://" in url:
            scheme, rest = url.split("://", 1)
            creds, hostdb = rest.split("@", 1)
            if ":" in creds:
                user, _pwd = creds.split(":", 1)
                creds_masked = f"{user}:***"
            else:
                creds_masked = creds
            return f"{scheme}://{creds_masked}@{hostdb}"
    except Exception:
        pass
    return url


@app.get("/api/matches")
async def get_matches() -> List[Dict[str, Any]]:
    try:
        df = fetch_dota_data_from_api()

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
        # Pretty format for days-ago
        def format_days_ago_pretty(days_ago, date_val):
            try:
                days = abs(float(days_ago))
            except Exception:
                return None
            if days < 1:
                try:
                    delta_hours = int(max(1, round(abs((datetime.now() - date_val).total_seconds()) / 3600)))
                except Exception:
                    delta_hours = 0
                return f"{delta_hours} hour{'s' if delta_hours != 1 else ''} ago" if delta_hours else "today"
            if days < 7:
                d = int(round(days))
                return f"{d} day{'s' if d != 1 else ''} ago"
            if days < 30:
                weeks = int(round(days / 7))
                return f"{weeks} week{'s' if weeks != 1 else ''} ago"
            months = int(round(days / 30))
            return f"{months} month{'s' if months != 1 else ''} ago"

        try:
            df['days_ago_pretty'] = df.apply(lambda r: format_days_ago_pretty(r.get('days_ago'), r.get('date')), axis=1)
        except Exception:
            df['days_ago_pretty'] = None

        df = df.sort_values('final_score', ascending=False)

        # Add user ratings from database
        db = SessionLocal()
        try:
            rated_matches = {str(r.match_id): r for r in db.query(MatchRating).all()}
            df['user_score'] = df['match_id'].map(lambda mid: getattr(rated_matches.get(str(mid)), 'score', None))
            df['user_title'] = df['match_id'].map(lambda mid: getattr(rated_matches.get(str(mid)), 'title', ''))
        finally:
            db.close()

        # Select columns
        df_scores = df[SCORES_COLS + ['user_score', 'user_title']]

        # Persist to latest_matches table
        session = SessionLocal()
        try:
            session.query(LatestMatch).delete()
            objects = []
            for _, row in df_scores.head(100).iterrows():
                objects.append(
                    LatestMatch(
                        match_id=str(row['match_id']),
                        title=row.get('title'),
                        days_ago=float(row['days_ago']) if pd.notna(row['days_ago']) else None,
                        days_ago_pretty=row.get('days_ago_pretty'),
                        final_score=float(row['final_score']) if pd.notna(row['final_score']) else None,
                        first_fight_at=row.get('first_fight_at') if 'first_fight_at' in row else None,
                        tournament=row.get('tournament'),
                        radiant_team_name=row.get('radiant_team_name'),
                        dire_team_name=row.get('dire_team_name'),
                        duration_min=int(row['duration_min']) if pd.notna(row['duration_min']) else None,
                        user_score=int(row['user_score']) if pd.notna(row['user_score']) else None,
                        user_title=row.get('user_title'),
                    )
                )
            if objects:
                session.bulk_save_objects(objects)
            session.commit()
        finally:
            session.close()

        # Return from the persisted table
        session = SessionLocal()
        try:
            rows = (
                session.query(LatestMatch)
                .order_by(LatestMatch.final_score.desc().nulls_last())
                .limit(100)
                .all()
            )
            return [
                {
                    "match_id": r.match_id,
                    "title": r.title,
                    "days_ago": r.days_ago,
                    "days_ago_pretty": r.days_ago_pretty,
                    "final_score": r.final_score,
                    "first_fight_at": r.first_fight_at,
                    "tournament": r.tournament,
                    "radiant_team_name": r.radiant_team_name,
                    "dire_team_name": r.dire_team_name,
                    "duration_min": r.duration_min,
                    "user_score": r.user_score,
                    "user_title": r.user_title,
                }
                for r in rows
            ]
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recalculate")
async def recalculate():
    # This endpoint is kept for backward compatibility but does nothing
    # since we fetch fresh data on each request to /api/matches
    return {"status": "success"}


def _refresh_cached_matches(days_limit: int = 100) -> int:
    """Fetch latest matches, keep last N days, upsert into cached_matches, prune old rows."""
    session = SessionLocal()
    upserted = 0
    try:
        df = fetch_dota_data_from_api()
        df = clean_df_and_fill_nas(df)
        df['watched'] = False
        df = calculate_all_game_statistics(df)
        df = calculate_scores(df)

        # Filter to recent window
        try:
            df['days_ago'] = pd.to_numeric(df.get('days_ago'), errors='coerce')
            df = df[(df['days_ago'] >= 0) & (df['days_ago'] <= days_limit)]
        except Exception:
            pass

        # Compute pretty days-ago
        def format_days_ago_pretty(days_ago, date_val):
            try:
                days = abs(float(days_ago))
            except Exception:
                days = None
            if days is not None:
                if days < 1:
                    try:
                        delta_hours = int(max(1, round(abs((datetime.now() - date_val).total_seconds()) / 3600))) if date_val is not None else 0
                    except Exception:
                        delta_hours = 0
                    return f"{delta_hours} hour{'s' if delta_hours != 1 else ''} ago" if delta_hours else "today"
                if days < 7:
                    d = int(round(days))
                    return f"{d} day{'s' if d != 1 else ''} ago"
                if days < 30:
                    weeks = int(round(days / 7))
                    return f"{weeks} week{'s' if weeks != 1 else ''} ago"
                months = int(round(days / 30))
                return f"{months} month{'s' if months != 1 else ''} ago"
            try:
                if isinstance(date_val, datetime):
                    delta = datetime.now() - date_val
                    days = delta.days
                    if days < 7:
                        return f"{days} day{'s' if days != 1 else ''} ago"
                    if days < 30:
                        weeks = int(round(days / 7))
                        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
                    months = int(round(days / 30))
                    return f"{months} month{'s' if months != 1 else ''} ago"
            except Exception:
                pass
            return None

        try:
            df['days_ago_pretty'] = df.apply(lambda r: format_days_ago_pretty(r.get('days_ago'), r.get('date')), axis=1)
        except Exception:
            pass

        # Select columns
        cols = ['match_id', 'title', 'days_ago', 'days_ago_pretty', 'final_score', 'tournament', 'radiant_team_name', 'dire_team_name', 'duration_min']
        missing = [c for c in cols if c not in df.columns]
        for c in missing:
            df[c] = None
        df_sel = df[cols].copy()

        # Upsert and prune
        for _, row in df_sel.iterrows():
            mid = str(row['match_id']) if pd.notna(row['match_id']) else None
            if not mid:
                continue
            existing = session.query(CachedMatch).filter(CachedMatch.match_id == mid).first()
            if existing:
                existing.title = row['title'] if pd.notna(row['title']) else existing.title
                existing.final_score = float(row['final_score']) if pd.notna(row['final_score']) else existing.final_score
                existing.days_ago = float(row['days_ago']) if pd.notna(row['days_ago']) else existing.days_ago
                existing.days_ago_pretty = row['days_ago_pretty'] if pd.notna(row['days_ago_pretty']) else existing.days_ago_pretty
                existing.tournament = row['tournament'] if pd.notna(row['tournament']) else existing.tournament
                existing.radiant_team_name = row['radiant_team_name'] if pd.notna(row['radiant_team_name']) else existing.radiant_team_name
                existing.dire_team_name = row['dire_team_name'] if pd.notna(row['dire_team_name']) else existing.dire_team_name
                existing.duration_min = int(row['duration_min']) if pd.notna(row['duration_min']) else existing.duration_min
            else:
                session.add(CachedMatch(
                    match_id=mid,
                    title=row['title'] if pd.notna(row['title']) else None,
                    final_score=float(row['final_score']) if pd.notna(row['final_score']) else None,
                    days_ago=float(row['days_ago']) if pd.notna(row['days_ago']) else None,
                    days_ago_pretty=row['days_ago_pretty'] if pd.notna(row['days_ago_pretty']) else None,
                    tournament=row['tournament'] if pd.notna(row['tournament']) else None,
                    radiant_team_name=row['radiant_team_name'] if pd.notna(row['radiant_team_name']) else None,
                    dire_team_name=row['dire_team_name'] if pd.notna(row['dire_team_name']) else None,
                    duration_min=int(row['duration_min']) if pd.notna(row['duration_min']) else None,
                ))
            upserted += 1

        # Prune rows older than window
        try:
            session.query(CachedMatch).filter(CachedMatch.days_ago > days_limit).delete()
        except Exception:
            pass

        session.commit()
        return upserted
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@app.get("/api/matches_cached")
async def get_matches_cached(limit: int = 100, background_tasks: BackgroundTasks = None) -> List[Dict[str, Any]]:
    try:
        db = SessionLocal()
        try:
            # Fetch cached matches ordered by final_score desc, handling NULLs
            rows = (
                db.query(CachedMatch)
                .order_by(CachedMatch.final_score.desc().nulls_last())
                .limit(limit)
                .all()
            )

            # Map to dicts with expected fields
            base = [
                {
                    "match_id": r.match_id,
                    "title": r.title,
                    "days_ago": r.days_ago,
                    "days_ago_pretty": r.days_ago_pretty,
                    "final_score": r.final_score,
                    "first_fight_at": None,
                    "tournament": r.tournament,
                    "radiant_team_name": r.radiant_team_name,
                    "dire_team_name": r.dire_team_name,
                    "duration_min": r.duration_min,
                }
                for r in rows
            ]

            # Add user ratings from database
            rated_matches = {str(r.match_id): r for r in db.query(MatchRating).all()}
            for item in base:
                rid = str(item["match_id"]) if item.get("match_id") is not None else None
                rating = rated_matches.get(rid) if rid is not None else None
                item["user_score"] = getattr(rating, "score", None)
                item["user_title"] = getattr(rating, "title", "")

            # Fire-and-forget refresh to keep cache warm (last 100 days)
            if background_tasks is not None:
                background_tasks.add_task(_refresh_cached_matches, 100)

            # If cache empty, fall back to live fetch synchronously
            if not base:
                try:
                    _refresh_cached_matches(100)
                    rows = (
                        db.query(CachedMatch)
                        .order_by(CachedMatch.final_score.desc().nulls_last())
                        .limit(limit)
                        .all()
                    )
                    base = [
                        {
                            "match_id": r.match_id,
                            "title": r.title,
                            "days_ago": r.days_ago,
                            "days_ago_pretty": r.days_ago_pretty,
                            "final_score": r.final_score,
                            "first_fight_at": None,
                            "tournament": r.tournament,
                            "radiant_team_name": r.radiant_team_name,
                            "dire_team_name": r.dire_team_name,
                            "duration_min": r.duration_min,
                            "user_score": getattr(rated_matches.get(str(r.match_id)), "score", None),
                            "user_title": getattr(rated_matches.get(str(r.match_id)), "title", ""),
                        }
                        for r in rows
                    ]
                except Exception:
                    pass

            return base
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rate_match")
async def rate_match(request: RateMatchRequest, db: Session = Depends(get_db)):
    try:
        match_id = str(request.match_id)

        # Derive the current match title from the computed dataset
        try:
            df = fetch_dota_data_from_api()
            df = clean_df_and_fill_nas(df)
            df['watched'] = False
            df = calculate_all_game_statistics(df)
            # Find the row with this match_id
            row = df.loc[df['match_id'] == int(request.match_id)]
            derived_title = None
            if not row.empty:
                derived_title = row.iloc[0].get('title')
        except Exception:
            derived_title = None

        # Check if rating exists
        rating = db.query(MatchRating).filter(MatchRating.match_id == match_id).first()

        if rating:
            # Update existing rating
            rating.score = request.score
            if derived_title:
                rating.title = derived_title
        else:
            # Create new rating
            rating = MatchRating(
                match_id=match_id,
                title=derived_title or "",
                score=request.score
            )
            db.add(rating)

        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratings")
async def list_ratings(limit: int = 50, db: Session = Depends(get_db)):
    try:
        qs = db.query(MatchRating).order_by(MatchRating.created_at.desc()).limit(limit).all()
        return [
            {
                "match_id": r.match_id,
                "title": r.title,
                "score": r.score,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in qs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
