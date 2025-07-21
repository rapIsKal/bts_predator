import pytest

from main import contains_korean_and_arbeit_macht_frei


@pytest.mark.parametrize("text", [
    "ищулюдейнаподработку",
    "заработай10.000руб",
    "ищуребятзаработок1000р",
    "ищулюдейнаработуза5k₽",
    "ищулюдейнаработуза5k rub",
    "5000рубработа",
    "ищуработусзарплатой15тыср",
    "10.000 руб."
])
def test_spam_detected(text):
    assert contains_korean_and_arbeit_macht_frei(text) is True