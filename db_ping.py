from sqlalchemy import text
from database import engine, init_db
import os


def main():
    print("Initializing database and testing connectivity...")
    try:
        init_db()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"DB connection OK, SELECT 1 -> {val}")
            # Show masked connection info
            url = os.getenv("DATABASE_URL", "")
            if url:
                print("DATABASE_URL present (masked):", mask_url(url))
            # Check for match_ratings table and count rows
            try:
                count_result = conn.execute(text("SELECT COUNT(*) FROM match_ratings"))
                count_val = count_result.scalar()
                print(f"Table match_ratings exists. Row count: {count_val}")
            except Exception as e:
                print(f"Table match_ratings not found or inaccessible: {e}")
    except Exception as e:
        print(f"DB connection failed: {e}")
        raise


if __name__ == "__main__":
    def mask_url(url: str) -> str:
        # Mask password segment in URL for safe printing
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

    main()
