import os

import pandas as pd
from flask import Flask, jsonify, render_template

from constants import SCORES_CSV_FILE, SCORES_COLS
from dota.get_and_score_func import get_and_score_func

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/matches')
def get_matches():
    try:
        # Check if scores file exists, if not generate it
        if not os.path.exists(SCORES_CSV_FILE):
            get_and_score_func()

        # Read and return the scores
        df = pd.read_csv(SCORES_CSV_FILE)
        # Convert to list of dicts for JSON response
        matches = df[SCORES_COLS].to_dict('records')
        return jsonify(matches)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recalculate', methods=['POST'])
def recalculate():
    try:
        # Trigger recalculation
        get_and_score_func()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
