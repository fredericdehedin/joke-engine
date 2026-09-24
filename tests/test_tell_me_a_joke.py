from types import SimpleNamespace

import anthropic
import httpx2
from dotenv import load_dotenv

import tell_me_a_joke


class FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception
        self.create_kwargs = None

    def create(self, **kwargs):
        self.create_kwargs = kwargs
        if self._exception is not None:
            raise self._exception
        return self._response


class FakeClient:
    def __init__(self, messages):
        self.messages = messages


def _text_response(text):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


def _fake_request():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def test_main_prints_generated_joke(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "cats")
    fake_messages = FakeMessages(response=_text_response("Why did the cat sit on the keyboard? To keep an eye on the mouse."))
    monkeypatch.setattr(tell_me_a_joke.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    tell_me_a_joke.main()

    out = capsys.readouterr().out
    assert "Why did the cat sit on the keyboard? To keep an eye on the mouse." in out
    assert "i got the topic" not in out


def test_main_prints_error_message_on_api_failure(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt="": "cats")
    fake_messages = FakeMessages(exception=anthropic.APIConnectionError(request=_fake_request()))
    monkeypatch.setattr(tell_me_a_joke.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    tell_me_a_joke.main()

    out = capsys.readouterr().out
    assert "couldn't come up with a joke" in out
    assert "Why did" not in out


def test_default_model_and_effort_are_cost_efficient(monkeypatch):
    monkeypatch.delenv("JOKE_ENGINE_MODEL", raising=False)
    monkeypatch.delenv("JOKE_ENGINE_EFFORT", raising=False)
    fake_messages = FakeMessages(response=_text_response("a joke"))
    monkeypatch.setattr(tell_me_a_joke.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    tell_me_a_joke.generate_joke("cats")

    assert fake_messages.create_kwargs["model"] == "claude-haiku-4-5"
    assert "output_config" not in fake_messages.create_kwargs


def test_model_and_effort_overrides_are_applied(monkeypatch):
    monkeypatch.setenv("JOKE_ENGINE_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("JOKE_ENGINE_EFFORT", "high")
    fake_messages = FakeMessages(response=_text_response("a joke"))
    monkeypatch.setattr(tell_me_a_joke.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    tell_me_a_joke.generate_joke("cats")

    assert fake_messages.create_kwargs["model"] == "claude-sonnet-5"
    assert fake_messages.create_kwargs["output_config"] == {"effort": "high"}


def test_env_var_from_dotenv_file_is_picked_up(tmp_path, monkeypatch):
    monkeypatch.delenv("JOKE_ENGINE_MODEL", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("JOKE_ENGINE_MODEL=claude-opus-5\n")

    try:
        load_dotenv(dotenv_path=env_file)
        assert tell_me_a_joke.resolve_model() == "claude-opus-5"
    finally:
        monkeypatch.delenv("JOKE_ENGINE_MODEL", raising=False)


def test_existing_env_var_takes_precedence_over_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.setenv("JOKE_ENGINE_MODEL", "claude-sonnet-5")
    env_file = tmp_path / ".env"
    env_file.write_text("JOKE_ENGINE_MODEL=claude-opus-5\n")

    load_dotenv(dotenv_path=env_file)

    assert tell_me_a_joke.resolve_model() == "claude-sonnet-5"
