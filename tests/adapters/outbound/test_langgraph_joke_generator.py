from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from joke_engine.adapters.outbound import langgraph_joke_generator
from joke_engine.adapters.outbound.langgraph_joke_generator import LangGraphJokeGenerator
from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError, JokeGenerator


class FakeChatModel:
    last_instance = None

    def __init__(self, response=None, exception=None, **kwargs):
        self._response = response
        self._exception = exception
        self.init_kwargs = kwargs
        self.invoked_messages = None
        FakeChatModel.last_instance = self

    def invoke(self, messages):
        self.invoked_messages = messages
        if self._exception is not None:
            raise self._exception
        return SimpleNamespace(content=self._response)


def _fake_chat_model_factory(response=None, exception=None):
    def factory(**kwargs):
        return FakeChatModel(response=response, exception=exception, **kwargs)

    return factory


def _fake_request():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def test_langgraph_joke_generator_satisfies_protocol():
    assert isinstance(LangGraphJokeGenerator(), JokeGenerator)


def test_start_returns_generation_with_one_revision(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator,
        "ChatAnthropic",
        _fake_chat_model_factory(response="Why did the cat sit on the keyboard?"),
    )

    generation = LangGraphJokeGenerator().start("cats")

    assert generation.topic == "cats"
    assert len(generation.revisions) == 1
    assert generation.revisions[0].style is None
    assert generation.revisions[0].joke.text == "Why did the cat sit on the keyboard?"
    system_message, human_message = FakeChatModel.last_instance.invoked_messages
    assert system_message.content == langgraph_joke_generator.SYSTEM_PROMPT
    assert "cats" in human_message.content


@pytest.mark.parametrize(
    "style",
    [RewriteStyle.DARK_CRUDE, RewriteStyle.CLEAN_CLEVER],
)
def test_refine_appends_revision_with_style_prompt(monkeypatch, style):
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="a rewritten joke")
    )
    generation = JokeGeneration(
        topic="cats",
        revisions=(Revision(joke=Joke(topic="cats", text="original joke"), style=None),),
    )

    refined = LangGraphJokeGenerator().refine(generation, style)

    assert len(refined.revisions) == 2
    assert refined.revisions[-1].style is style
    assert refined.revisions[-1].joke.text == "a rewritten joke"
    system_message, human_message = FakeChatModel.last_instance.invoked_messages
    assert system_message.content == langgraph_joke_generator.REWRITE_SYSTEM_PROMPTS[style]
    assert human_message.content == "original joke"


def test_start_wraps_api_failure_in_joke_generation_error(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator,
        "ChatAnthropic",
        _fake_chat_model_factory(exception=anthropic.APIConnectionError(request=_fake_request())),
    )

    with pytest.raises(JokeGenerationError):
        LangGraphJokeGenerator().start("cats")


def test_refine_wraps_api_failure_in_joke_generation_error(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator,
        "ChatAnthropic",
        _fake_chat_model_factory(exception=anthropic.APIConnectionError(request=_fake_request())),
    )
    generation = JokeGeneration(
        topic="cats",
        revisions=(Revision(joke=Joke(topic="cats", text="original joke"), style=None),),
    )

    with pytest.raises(JokeGenerationError):
        LangGraphJokeGenerator().refine(generation, RewriteStyle.DARK_CRUDE)


def test_default_model_and_effort_are_cost_efficient(monkeypatch):
    monkeypatch.delenv("JOKE_ENGINE_MODEL", raising=False)
    monkeypatch.delenv("JOKE_ENGINE_EFFORT", raising=False)
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="a joke")
    )

    LangGraphJokeGenerator().start("cats")

    assert FakeChatModel.last_instance.init_kwargs["model"] == "claude-haiku-4-5"
    assert "output_config" not in FakeChatModel.last_instance.init_kwargs


def test_model_and_effort_overrides_are_applied(monkeypatch):
    monkeypatch.setenv("JOKE_ENGINE_MODEL", "claude-sonnet-5")
    monkeypatch.setenv("JOKE_ENGINE_EFFORT", "high")
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="a joke")
    )

    LangGraphJokeGenerator().start("cats")

    assert FakeChatModel.last_instance.init_kwargs["model"] == "claude-sonnet-5"
    assert FakeChatModel.last_instance.init_kwargs["output_config"] == {"effort": "high"}
