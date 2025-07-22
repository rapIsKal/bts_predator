import pytest

from model_predict import predict


@pytest.mark.parametrize("text", [
    "ищу людей на подработку",
    "заработай 10.000руб",
    "ищу ребят заработок 1000р",
    "ищу людей на работу за 5k₽",
    "ищу людей на работу за 5k rub",
    "5000 руб работа",
    "ищу работу с зарплатой 15тыср",
    "10.000 руб.",
    "10000 руб",
    "Ищешь работу го в ЛС"
])
def test_spam_detect_with_model_trained(text):
    label, _ = predict(text)
    assert label == 1
