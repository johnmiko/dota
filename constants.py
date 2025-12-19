import os

# Teams configuration
TEAMS_I_LIKE = ['Team Liquid', 'Team Spirit', 'Tundra Esports', 'Team Falcons']
TEAM_ABBR = {
    'betboom': 'bb',
    'gaimin gladiators': 'gg',
    'evil geniuses': 'eg'
}

# Score configuration
FINAL_SCORE_COLS = ['interesting_score', 'days_ago_score', 'good_team_playing_score', 'aegis_steals_score']
WHOLE_GAME_SCORE_COLS = [
    'swing_score', 
    'fight_%_of_game_score', 
    'days_ago_score',
    'good_team_playing_score'
]
SCORES_COLS = [
    'match_id', 
    'title', 
    'time_ago', 
    'final_score', 
    'first_fight_at', 
    'tournament'
]
