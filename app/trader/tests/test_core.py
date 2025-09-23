from mirai_trader.core import signal_score


def test_signal_score_positive():
    assert signal_score(105, 100, 50) == 0.8


def test_signal_score_negative():
    assert signal_score(95, 100, 35) == 0.4
