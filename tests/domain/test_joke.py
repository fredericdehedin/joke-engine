import pytest

from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle


def test_joke_holds_topic_and_text():
    joke = Joke(topic="cats", text="Why did the cat sit on the keyboard?")

    assert joke.topic == "cats"
    assert joke.text == "Why did the cat sit on the keyboard?"


@pytest.mark.parametrize("topic,text", [("", "a joke"), ("cats", ""), ("  ", "a joke")])
def test_joke_rejects_blank_fields(topic, text):
    with pytest.raises(ValueError):
        Joke(topic=topic, text=text)


def _joke(text="a joke"):
    return Joke(topic="cats", text=text)


def test_joke_generation_holds_topic_and_revisions():
    revisions = (
        Revision(joke=_joke("first"), style=None),
        Revision(joke=_joke("second"), style=RewriteStyle.DARK_CRUDE),
    )

    generation = JokeGeneration(topic="cats", revisions=revisions)

    assert generation.topic == "cats"
    assert generation.revisions[-1].joke.text == "second"
    assert generation.revisions[-1].style is RewriteStyle.DARK_CRUDE


def test_joke_generation_rejects_blank_topic():
    with pytest.raises(ValueError):
        JokeGeneration(topic="", revisions=(Revision(joke=_joke(), style=None),))


def test_joke_generation_rejects_empty_revisions():
    with pytest.raises(ValueError):
        JokeGeneration(topic="cats", revisions=())


def test_joke_generation_rejects_first_revision_with_a_style():
    with pytest.raises(ValueError):
        JokeGeneration(
            topic="cats",
            revisions=(Revision(joke=_joke(), style=RewriteStyle.CLEAN_CLEVER),),
        )


def test_joke_generation_rejects_later_revision_without_a_style():
    with pytest.raises(ValueError):
        JokeGeneration(
            topic="cats",
            revisions=(
                Revision(joke=_joke("first"), style=None),
                Revision(joke=_joke("second"), style=None),
            ),
        )
