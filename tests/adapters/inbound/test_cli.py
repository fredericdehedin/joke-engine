from joke_engine.adapters.inbound import cli
from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError


class FakeJokeGenerator:
    def __init__(self, texts=None, start_exception=None, refine_exception=None):
        self._texts = iter(texts or [])
        self._start_exception = start_exception
        self._refine_exception = refine_exception
        self.refine_calls = []

    def start(self, topic):
        if self._start_exception is not None:
            raise self._start_exception
        joke = Joke(topic=topic, text=next(self._texts))
        return JokeGeneration(topic=topic, revisions=(Revision(joke=joke, style=None),))

    def refine(self, generation, style):
        self.refine_calls.append(style)
        if self._refine_exception is not None:
            raise self._refine_exception
        joke = Joke(topic=generation.topic, text=next(self._texts))
        return JokeGeneration(
            topic=generation.topic,
            revisions=generation.revisions + (Revision(joke=joke, style=style),),
        )


def _inputs(*values):
    responses = iter(values)
    return lambda prompt="": next(responses)


def test_main_accepts_first_joke_and_prints_it(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["Why did the cat sit on the keyboard?"])
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats", "a"))

    cli.main()

    out = capsys.readouterr().out
    assert "Why did the cat sit on the keyboard?" in out


def test_main_refines_then_accepts_prints_revised_joke(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke", "second joke"])
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats", "d", "a"))

    cli.main()

    out = capsys.readouterr().out
    assert "second joke" in out
    assert "first joke" not in out
    assert fake_generator.refine_calls == [RewriteStyle.DARK_CRUDE]


def test_main_supports_multiple_rounds_of_revision(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first", "second", "third"])
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats", "d", "c", "a"))

    cli.main()

    out = capsys.readouterr().out
    assert "third" in out
    assert fake_generator.refine_calls == [RewriteStyle.DARK_CRUDE, RewriteStyle.CLEAN_CLEVER]


def test_main_quits_without_printing_any_joke(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["Why did the cat sit on the keyboard?"])
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats", "q"))

    cli.main()

    out = capsys.readouterr().out
    assert "Why did the cat sit on the keyboard?" not in out


def test_main_prints_error_message_on_start_failure(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(start_exception=JokeGenerationError("no credentials configured"))
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats"))

    cli.main()

    out = capsys.readouterr().out
    assert "couldn't come up with a joke" in out


def test_main_prints_error_message_on_refine_failure_after_one_round(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"], refine_exception=JokeGenerationError("boom"))
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: fake_generator)
    monkeypatch.setattr("builtins.input", _inputs("cats", "d"))

    cli.main()

    out = capsys.readouterr().out
    assert "couldn't come up with a joke" in out
    assert "first joke" not in out
