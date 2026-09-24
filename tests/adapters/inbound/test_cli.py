from types import SimpleNamespace

from joke_engine.adapters.inbound import cli
from joke_engine.adapters.outbound import anthropic_joke_generator


class FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    def create(self, **kwargs):
        if self._exception is not None:
            raise self._exception
        return self._response


class FakeClient:
    def __init__(self, messages):
        self.messages = messages


def _text_response(text):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def test_main_prints_generated_joke(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "cats")
    fake_messages = FakeMessages(response=_text_response("Why did the cat sit on the keyboard? To keep an eye on the mouse."))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    cli.main()

    out = capsys.readouterr().out
    assert "Why did the cat sit on the keyboard? To keep an eye on the mouse." in out


def test_main_prints_error_message_on_generation_failure(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "cats")
    fake_messages = FakeMessages(exception=RuntimeError("no credentials configured"))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    cli.main()

    out = capsys.readouterr().out
    assert "couldn't come up with a joke" in out
    assert "Why did" not in out
