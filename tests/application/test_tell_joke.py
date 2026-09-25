import pytest

from joke_engine.application.tell_joke import TellJokeUseCase
from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError


class FakeJokeGenerator:
    def __init__(self, generation=None, exception=None):
        self._generation = generation
        self._exception = exception
        self.requested_topic = None
        self.requested_generation = None
        self.requested_style = None

    def start(self, topic: str) -> JokeGeneration:
        self.requested_topic = topic
        if self._exception is not None:
            raise self._exception
        return self._generation

    def refine(self, generation: JokeGeneration, style: RewriteStyle) -> JokeGeneration:
        self.requested_generation = generation
        self.requested_style = style
        if self._exception is not None:
            raise self._exception
        return self._generation


def _generation(text="Why did the cat sit on the keyboard?"):
    return JokeGeneration(
        topic="cats",
        revisions=(Revision(joke=Joke(topic="cats", text=text), style=None),),
    )


def test_start_returns_generation_from_generator():
    generator = FakeJokeGenerator(generation=_generation())
    use_case = TellJokeUseCase(generator)

    generation = use_case.start("cats")

    assert generator.requested_topic == "cats"
    assert generation.revisions[-1].joke.text == "Why did the cat sit on the keyboard?"


def test_start_propagates_generation_errors():
    generator = FakeJokeGenerator(exception=JokeGenerationError("boom"))
    use_case = TellJokeUseCase(generator)

    with pytest.raises(JokeGenerationError):
        use_case.start("cats")


def test_refine_returns_generation_from_generator():
    generator = FakeJokeGenerator(generation=_generation("a rewritten joke"))
    use_case = TellJokeUseCase(generator)
    prior_generation = _generation()

    generation = use_case.refine(prior_generation, RewriteStyle.DARK_CRUDE)

    assert generator.requested_generation is prior_generation
    assert generator.requested_style is RewriteStyle.DARK_CRUDE
    assert generation.revisions[-1].joke.text == "a rewritten joke"


def test_refine_propagates_generation_errors():
    generator = FakeJokeGenerator(exception=JokeGenerationError("boom"))
    use_case = TellJokeUseCase(generator)

    with pytest.raises(JokeGenerationError):
        use_case.refine(_generation(), RewriteStyle.CLEAN_CLEVER)
