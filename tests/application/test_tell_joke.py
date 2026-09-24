import pytest

from joke_engine.application.tell_joke import TellJokeUseCase
from joke_engine.ports.joke_generator import JokeGenerationError


class FakeJokeGenerator:
    def __init__(self, text=None, exception=None):
        self._text = text
        self._exception = exception
        self.requested_topic = None

    def generate(self, topic: str) -> str:
        self.requested_topic = topic
        if self._exception is not None:
            raise self._exception
        return self._text


def test_execute_returns_joke_from_generator():
    generator = FakeJokeGenerator(text="Why did the cat sit on the keyboard?")
    use_case = TellJokeUseCase(generator)

    joke = use_case.execute("cats")

    assert generator.requested_topic == "cats"
    assert joke.topic == "cats"
    assert joke.text == "Why did the cat sit on the keyboard?"


def test_execute_propagates_generation_errors():
    generator = FakeJokeGenerator(exception=JokeGenerationError("boom"))
    use_case = TellJokeUseCase(generator)

    with pytest.raises(JokeGenerationError):
        use_case.execute("cats")
