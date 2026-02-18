from constants import SCORES_COLS, FINAL_SCORE_COLS, WHOLE_GAME_SCORE_COLS


def test_constants_have_expected_core_fields():
    assert "match_id" in SCORES_COLS
    assert "title" in SCORES_COLS
    assert "final_score" in SCORES_COLS

    assert "interesting_score" in FINAL_SCORE_COLS
    assert "days_ago_score" in FINAL_SCORE_COLS

    assert "swing_score" in WHOLE_GAME_SCORE_COLS
