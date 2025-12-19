import os
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import engine, SessionLocal, CachedMatch

load_dotenv()

CSV_PATH = os.getenv("SCORES_CSV_PATH", "text/scores_all_cols.csv")
DAYS_LIMIT = int(os.getenv("SCORES_DAYS_LIMIT", "30"))


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
	# Fallback: if days_ago not available, compute from date
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


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
	# Standardize expected columns if present under alternate names
	if 'duration' in df.columns and 'duration_min' not in df.columns:
		df['duration_min'] = df['duration']
	return df


def import_csv(csv_path: str, days_limit: int):
	print(f"Loading CSV from {csv_path} ...")
	df = pd.read_csv(csv_path, low_memory=False)
	# Parse date column if present
	if 'date' in df.columns:
		try:
			df['date'] = pd.to_datetime(df['date'], errors='coerce')
		except Exception:
			pass
	df = normalize_columns(df)

	# Filter last N days by 'days_ago' if available, else by 'date'
	if 'days_ago' in df.columns:
		try:
			df['days_ago'] = pd.to_numeric(df['days_ago'], errors='coerce')
			df = df[(df['days_ago'] >= 0) & (df['days_ago'] <= days_limit)]
		except Exception:
			pass
	elif 'date' in df.columns:
		try:
			cutoff = datetime.now() - timedelta(days=days_limit)
			df = df[df['date'] >= cutoff]
		except Exception:
			pass

	# Compute pretty days-ago
	if 'days_ago_pretty' not in df.columns:
		df['days_ago_pretty'] = df.apply(lambda r: format_days_ago_pretty(r.get('days_ago'), r.get('date')), axis=1)

	# Select columns we care about
	cols = [
		'match_id', 'title', 'final_score', 'days_ago', 'days_ago_pretty', 'tournament',
		'radiant_team_name', 'dire_team_name', 'duration_min'
	]
	missing = [c for c in cols if c not in df.columns]
	if missing:
		print(f"Warning: Missing columns in CSV: {missing}")
		for c in missing:
			df[c] = None
	df_small = df[cols].copy()

	# Coerce types
	def coerce_float(s):
		try:
			return float(s)
		except Exception:
			return None
	df_small['final_score'] = df_small['final_score'].apply(coerce_float)
	df_small['days_ago'] = df_small['days_ago'].apply(coerce_float)
	try:
		df_small['duration_min'] = pd.to_numeric(df_small['duration_min'], errors='coerce').astype('Int64')
	except Exception:
		pass

	# Upsert into database
	session: Session = SessionLocal()
	upserted = 0
	try:
		for _, row in df_small.iterrows():
			mid = str(row['match_id']) if pd.notna(row['match_id']) else None
			if not mid:
				continue
			existing = session.query(CachedMatch).filter(CachedMatch.match_id == mid).first()
			if existing:
				existing.title = row['title'] if pd.notna(row['title']) else existing.title
				existing.final_score = row['final_score'] if pd.notna(row['final_score']) else existing.final_score
				existing.days_ago = row['days_ago'] if pd.notna(row['days_ago']) else existing.days_ago
				existing.days_ago_pretty = row['days_ago_pretty'] if pd.notna(row['days_ago_pretty']) else existing.days_ago_pretty
				existing.tournament = row['tournament'] if pd.notna(row['tournament']) else existing.tournament
				existing.radiant_team_name = row['radiant_team_name'] if pd.notna(row['radiant_team_name']) else existing.radiant_team_name
				existing.dire_team_name = row['dire_team_name'] if pd.notna(row['dire_team_name']) else existing.dire_team_name
				existing.duration_min = int(row['duration_min']) if pd.notna(row['duration_min']) else existing.duration_min
			else:
				session.add(CachedMatch(
					match_id=mid,
					title=row['title'] if pd.notna(row['title']) else None,
					final_score=row['final_score'] if pd.notna(row['final_score']) else None,
					days_ago=row['days_ago'] if pd.notna(row['days_ago']) else None,
					days_ago_pretty=row['days_ago_pretty'] if pd.notna(row['days_ago_pretty']) else None,
					tournament=row['tournament'] if pd.notna(row['tournament']) else None,
					radiant_team_name=row['radiant_team_name'] if pd.notna(row['radiant_team_name']) else None,
					dire_team_name=row['dire_team_name'] if pd.notna(row['dire_team_name']) else None,
					duration_min=int(row['duration_min']) if pd.notna(row['duration_min']) else None,
				))
			upserted += 1
		session.commit()
	except Exception as e:
		session.rollback()
		raise e
	finally:
		session.close()
	print(f"Upserted {upserted} rows into cached_matches.")


if __name__ == "__main__":
	import_csv(CSV_PATH, DAYS_LIMIT)
# Create a CSV import script for cached matches.