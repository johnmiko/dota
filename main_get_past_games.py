import pandas as pd
import requests

from constants import LAST_RUN_FILE, RAW_FILE
from dota.run_tracker import RunTracker

run_tracker = RunTracker(LAST_RUN_FILE)

# Need to manually update if I haven't been running the code for a while
# In excel just glance at the start times of the games and see where the largest dif is
# Well...Could subtract the times from the previous times and find the largest time gap
have_these_games_time = 1721937466

df = pd.read_csv(RAW_FILE)
for i in range(1, 100):
    min_start_time = df[df['start_time'] > 1721937466]["start_time"].min()
    if min_start_time <= have_these_games_time:
        break
    sql_query = f"""SELECT * 
        FROM matches
        JOIN leagues using(leagueid)
        WHERE name not like '%Division II%'
        AND leagues.TIER in ('professional','premium') 
        AND start_time < {int(min_start_time)}
        AND start_time > {have_these_games_time}
        ORDER BY matches.start_time DESC
        LIMIT 4000"""
    update_data = True
    if update_data:
        pass
    url = f"""https://api.opendota.com/api/explorer?sql={sql_query}"""
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        print(r.text)
    matches = r.json()['rows']
    df_new = pd.DataFrame(matches)
    df_raw = pd.read_csv(RAW_FILE)
    df = pd.concat([df_new, df_raw])
    df = df.drop_duplicates('match_id')
    df.to_csv(RAW_FILE, index=False, header=True)
    print(f"start time was {int(min_start_time)}")
    print(f"done iteration {i}")
print("finished")
