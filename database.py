from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env if present (for local dev)
load_dotenv()

# Get database URL from environment variable (Railway will provide this)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback to SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./dota_ratings.db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MatchRating(Base):
    __tablename__ = "match_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CachedMatch(Base):
    __tablename__ = "cached_matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    final_score = Column(Float, nullable=True)
    days_ago = Column(Float, nullable=True)
    days_ago_pretty = Column(String, nullable=True)
    tournament = Column(String, nullable=True)
    radiant_team_name = Column(String, nullable=True)
    dire_team_name = Column(String, nullable=True)
    duration_min = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LatestMatch(Base):
    __tablename__ = "latest_matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    days_ago = Column(Float, nullable=True)
    days_ago_pretty = Column(String, nullable=True)
    final_score = Column(Float, nullable=True)
    first_fight_at = Column(String, nullable=True)
    tournament = Column(String, nullable=True)
    radiant_team_name = Column(String, nullable=True)
    dire_team_name = Column(String, nullable=True)
    duration_min = Column(Integer, nullable=True)
    user_score = Column(Integer, nullable=True)
    user_title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def init_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        # Ensure 'title' is NOT NULL in Postgres (migration-lite)
        try:
            if engine.dialect.name == "postgresql":
                conn = engine.connect()
                conn.execute(text("ALTER TABLE match_ratings ALTER COLUMN title SET NOT NULL"))
                conn.close()
        except Exception:
            # Ignore if already set or on SQLite
            pass
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
