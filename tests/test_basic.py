import pytest

from main import contains_korean_and_arbeit_macht_frei

@pytest.mark.parametrize(("text", "result"), [
    ("ищу людей на подработку", True),
    ("заработай 10.000руб", True),
    ("ищу ребят заработок 1000р", True),
    ("ищу людей на работу за 5k₽", True),
    ("ищу людей на работу за 5k rub", True),
    ("5000 руб работа", True),
    ("ищу работу с зарплатой 15тыср", True),
    ("10.000 руб.", True),
    ("10000 руб", True),
    ("Ищешь работу го в ЛС", True),
    ("проработанный", False)
])
def test_spam_detected(text, result):
    assert contains_korean_and_arbeit_macht_frei(text) is result


