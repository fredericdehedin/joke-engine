import pytest

from joke_engine.domain.joke import Joke


def test_joke_holds_topic_and_text():
    joke = Joke(topic="cats", text="Why did the cat sit on the keyboard?")

    assert joke.topic == "cats"
    assert joke.text == "Why did the cat sit on the keyboard?"


@pytest.mark.parametrize("topic,text", [("", "a joke"), ("cats", ""), ("  ", "a joke")])
def test_joke_rejects_blank_fields(topic, text):
    with pytest.raises(ValueError):
        Joke(topic=topic, text=text)
