import pandas as pd
import requests

from constants import LAST_RUN_FILE, HISTORIC_FILE
from dota.run_tracker import RunTracker

run_tracker = RunTracker(LAST_RUN_FILE)

# Need to manually update if I haven't been running the code for a while
# In excel just glance at the start times of the games and see where the largest dif is
# Well...Could subtract the times from the previous times and find the largest time gap
have_these_games_time = 1765736521

df = pd.read_csv(HISTORIC_FILE)
min_start_time = df[df['start_time'] > have_these_games_time]["start_time"].min()
print(f"start time is {int(min_start_time)}")
while min_start_time > have_these_games_time:
    # the while loop doesn't exist because the min start time was already specified
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
    try:
        url = f"""https://api.opendota.com/api/explorer?sql={sql_query}"""
        r = requests.get(url, timeout=45)
        if r.status_code != 200:
            print(r.text)
    except ConnectionError:
        # if there's a timeout
        continue
    matches = r.json()['rows']
    df_new = pd.DataFrame(matches)
    df_raw = pd.read_csv(HISTORIC_FILE)
    df = pd.concat([df_new, df_raw])
    df = df.drop_duplicates('match_id')
    df.to_csv(HISTORIC_FILE, index=False, header=True)
    min_start_time = df[df['start_time'] > 1721937466]["start_time"].min()
    print(f"start time is {int(min_start_time)}")
print("finished")
