import pytest

from main import contains_korean_and_arbeit_macht_frei
from model_predict import predict


@pytest.mark.parametrize("text", [
    "ищулюдейнаподработку",
    "заработай10.000руб",
    "ищуребятзаработок1000р",
    "ищулюдейнаработуза5k₽",
    "ищулюдейнаработуза5k rub",
    "5000рубработа",
    "ищуработусзарплатой15тыср",
    "10.000 руб.",
    "10000 руб"
])
def test_spam_detected(text):
    assert contains_korean_and_arbeit_macht_frei(text) is True


@pytest.mark.parametrize("text", [
    "ищу людей на подработку",
    "заработай 10.000руб",
    "ищу ребят заработок 1000р",
    "ищу людей на работу за 5k₽",
    "ищу людей на работу за 5k rub",
    "5000 руб работа",
    "ищу работу с зарплатой 15тыср",
    "10.000 руб.",
    "10000 руб"
])
def test_spam_detect_with_model_trained(text):
    label, _ = predict(text)
    assert label == 1
