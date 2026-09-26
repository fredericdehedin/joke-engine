import pytest

from joke_engine.adapters.inbound import cli
from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError


class FakeJokeGenerator:
    def __init__(self, texts=None, start_exception=None, refine_exception=None):
        self._texts = iter(texts or [])
        self._start_exception = start_exception
        self._refine_exception = refine_exception
        self.start_calls = []
        self.refine_calls = []

    def start(self, topic):
        self.start_calls.append(topic)
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
    """Stand in for input(), echoing each prompt the way the real one does.

    Without the echo, prompt text never reaches capsys and assertions about
    what the user saw would pass whatever the CLI actually displayed.
    """
    responses = iter(values)

    def fake_input(prompt=""):
        print(prompt, end="")
        value = next(responses)
        if isinstance(value, type) and issubclass(value, BaseException):
            raise value()
        print(value)
        return value

    return fake_input


def _install(monkeypatch, generator, *inputs):
    monkeypatch.setattr(cli, "LangGraphJokeGenerator", lambda: generator)
    monkeypatch.setattr("builtins.input", _inputs(*inputs))


def test_main_accepts_first_joke_and_prints_it(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["Why did the cat sit on the keyboard?"])
    _install(monkeypatch, fake_generator, "cats", "a")

    cli.main()

    out = capsys.readouterr().out
    assert "Why did the cat sit on the keyboard?" in out
    assert fake_generator.refine_calls == []


def test_main_prints_each_joke_exactly_once(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"])
    _install(monkeypatch, fake_generator, "cats", "a")

    cli.main()

    out = capsys.readouterr().out
    assert out.count("first joke") == 1


def test_main_refines_then_accepts_prints_revised_joke(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke", "second joke"])
    _install(monkeypatch, fake_generator, "cats", "d", "a")

    cli.main()

    out = capsys.readouterr().out
    assert out.index("first joke") < out.index("second joke")
    assert out.count("second joke") == 1
    assert fake_generator.refine_calls == [RewriteStyle.DARK_CRUDE]


def test_main_supports_multiple_rounds_of_revision(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first", "second", "third"])
    _install(monkeypatch, fake_generator, "cats", "d", "c", "a")

    cli.main()

    out = capsys.readouterr().out
    assert "third" in out
    assert fake_generator.refine_calls == [RewriteStyle.DARK_CRUDE, RewriteStyle.CLEAN_CLEVER]


def test_main_quits_without_requesting_a_rewrite(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["Why did the cat sit on the keyboard?"])
    _install(monkeypatch, fake_generator, "cats", "q")

    cli.main()

    out = capsys.readouterr().out
    # The joke is shown before the menu, so quitting can't un-show it; what
    # quitting must not do is ask for another joke.
    assert out.count("Why did the cat sit on the keyboard?") == 1
    assert fake_generator.refine_calls == []


def test_main_reprompts_on_an_unrecognised_choice(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"])
    _install(monkeypatch, fake_generator, "cats", "x", "a")

    cli.main()

    out = capsys.readouterr().out
    assert "Please choose a, d, c, or q." in out
    assert fake_generator.refine_calls == []


def test_main_prints_error_message_on_start_failure(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(start_exception=JokeGenerationError("no credentials configured"))
    _install(monkeypatch, fake_generator, "cats")

    cli.main()

    out = capsys.readouterr().out
    assert "couldn't come up with a joke" in out


def test_main_keeps_the_current_joke_when_a_rewrite_fails(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"], refine_exception=JokeGenerationError("boom"))
    _install(monkeypatch, fake_generator, "cats", "d", "a")

    cli.main()

    out = capsys.readouterr().out
    assert "couldn't rewrite that one" in out
    # Back at the menu rather than out of the program, so "a" still accepts.
    assert fake_generator.refine_calls == [RewriteStyle.DARK_CRUDE]


def test_main_exits_cleanly_when_stdin_ends_at_the_menu(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"])
    _install(monkeypatch, fake_generator, "cats", EOFError)

    cli.main()

    assert "first joke" in capsys.readouterr().out
    assert fake_generator.refine_calls == []


def test_main_exits_without_generating_when_stdin_ends_at_the_topic_prompt(monkeypatch):
    fake_generator = FakeJokeGenerator(texts=["first joke"])
    _install(monkeypatch, fake_generator, EOFError)

    cli.main()

    assert fake_generator.start_calls == []


def test_main_reprompts_on_a_blank_topic(monkeypatch, capsys):
    fake_generator = FakeJokeGenerator(texts=["first joke"])
    _install(monkeypatch, fake_generator, "   ", "cats", "a")

    cli.main()

    out = capsys.readouterr().out
    assert "Please enter a topic." in out
    assert fake_generator.start_calls == ["cats"]


@pytest.mark.parametrize("choice,style", [("d", RewriteStyle.DARK_CRUDE), ("c", RewriteStyle.CLEAN_CLEVER)])
def test_main_maps_each_choice_to_its_style(monkeypatch, choice, style):
    fake_generator = FakeJokeGenerator(texts=["first joke", "rewritten"])
    _install(monkeypatch, fake_generator, "cats", choice, "a")

    cli.main()

    assert fake_generator.refine_calls == [style]
