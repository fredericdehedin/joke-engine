from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from joke_engine.adapters.outbound import anthropic_joke_generator
from joke_engine.adapters.outbound.anthropic_joke_generator import AnthropicJokeGenerator
from joke_engine.ports.joke_generator import JokeGenerationError


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


def test_generate_returns_text_from_response(monkeypatch):
    fake_messages = FakeMessages(response=_text_response("Why did the cat sit on the keyboard? To keep an eye on the mouse."))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    joke_text = AnthropicJokeGenerator().generate("cats")

    assert joke_text == "Why did the cat sit on the keyboard? To keep an eye on the mouse."


def test_generate_wraps_api_failure_in_joke_generation_error(monkeypatch):
    fake_messages = FakeMessages(exception=anthropic.APIConnectionError(request=_fake_request()))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    with pytest.raises(JokeGenerationError):
        AnthropicJokeGenerator().generate("cats")


def test_default_model_and_effort_are_cost_efficient(monkeypatch):
    monkeypatch.delenv("JOKE_ENGINE_MODEL", raising=False)
    monkeypatch.delenv("JOKE_ENGINE_EFFORT", raising=False)
    fake_messages = FakeMessages(response=_text_response("a joke"))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    AnthropicJokeGenerator().generate("cats")

    assert fake_messages.create_kwargs["model"] == "claude-haiku-4-5"
    assert "output_config" not in fake_messages.create_kwargs


def test_model_and_effort_overrides_are_applied(monkeypatch):
    monkeypatch.setenv("JOKE_ENGINE_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("JOKE_ENGINE_EFFORT", "high")
    fake_messages = FakeMessages(response=_text_response("a joke"))
    monkeypatch.setattr(anthropic_joke_generator.anthropic, "Anthropic", lambda: FakeClient(fake_messages))

    AnthropicJokeGenerator().generate("cats")

    assert fake_messages.create_kwargs["model"] == "claude-sonnet-5"
    assert fake_messages.create_kwargs["output_config"] == {"effort": "high"}
