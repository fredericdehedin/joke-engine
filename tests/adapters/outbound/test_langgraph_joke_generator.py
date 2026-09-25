import inspect
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
    instances = []

    def __init__(self, response=None, exception=None, **kwargs):
        self._response = response
        self._exception = exception
        self.init_kwargs = kwargs
        self.invoked_messages = None
        FakeChatModel.last_instance = self
        FakeChatModel.instances.append(self)

    def invoke(self, messages):
        self.invoked_messages = messages
        if self._exception is not None:
            raise self._exception
        return SimpleNamespace(content=self._response)


def _fake_chat_model_factory(response=None, exception=None):
    FakeChatModel.instances = []

    def factory(**kwargs):
        return FakeChatModel(response=response, exception=exception, **kwargs)

    return factory


def _fake_request():
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _a_generation(text="original joke"):
    return JokeGeneration(
        topic="cats",
        revisions=(Revision(joke=Joke(topic="cats", text=text), style=None),),
    )


def test_langgraph_joke_generator_satisfies_protocol():
    generator: JokeGenerator = LangGraphJokeGenerator()
    assert isinstance(generator, JokeGenerator)


@pytest.mark.parametrize("method_name", ["start", "refine"])
def test_adapter_methods_match_the_port_signature(method_name):
    # runtime_checkable isinstance() only checks that attributes of these names
    # exist, so compare parameters and annotations explicitly.
    expected = inspect.signature(getattr(JokeGenerator, method_name))
    actual = inspect.signature(getattr(LangGraphJokeGenerator, method_name))

    assert actual == expected


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


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("a joke", id="plain string"),
        pytest.param([{"type": "text", "text": "a joke"}], id="single text block"),
        pytest.param(
            [{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "a joke"}],
            id="thinking block first",
        ),
        pytest.param(
            [{"type": "text", "text": "a "}, {"type": "text", "text": "joke"}],
            id="several text blocks",
        ),
        pytest.param(
            [SimpleNamespace(type="thinking", thinking="hmm"), SimpleNamespace(type="text", text="a joke")],
            id="block objects",
        ),
    ],
)
def test_start_extracts_the_text_blocks_of_the_response(monkeypatch, content):
    # langchain_anthropic only hands back a plain string when the reply holds
    # exactly one text block; enabling effort/thinking adds a second block.
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response=content)
    )

    generation = LangGraphJokeGenerator().start("cats")

    assert generation.revisions[-1].joke.text == "a joke"


def test_refine_extracts_the_text_blocks_of_the_response(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator,
        "ChatAnthropic",
        _fake_chat_model_factory(
            response=[{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "a rewritten joke"}]
        ),
    )

    refined = LangGraphJokeGenerator().refine(_a_generation(), RewriteStyle.DARK_CRUDE)

    assert refined.revisions[-1].joke.text == "a rewritten joke"


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("   ", id="whitespace only"),
        pytest.param("", id="empty"),
        pytest.param([{"type": "thinking", "thinking": "hmm"}], id="no text block"),
    ],
)
def test_start_wraps_an_unusable_response_in_joke_generation_error(monkeypatch, content):
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response=content)
    )

    with pytest.raises(JokeGenerationError):
        LangGraphJokeGenerator().start("cats")


def test_refine_wraps_an_unusable_response_in_joke_generation_error(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="   ")
    )

    with pytest.raises(JokeGenerationError):
        LangGraphJokeGenerator().refine(_a_generation(), RewriteStyle.DARK_CRUDE)


def test_chat_model_is_reused_across_rounds(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="a joke")
    )
    generator = LangGraphJokeGenerator()

    generation = generator.start("cats")
    generator.refine(generation, RewriteStyle.DARK_CRUDE)

    assert len(FakeChatModel.instances) == 1


def test_chat_model_is_not_built_until_first_use(monkeypatch):
    monkeypatch.setattr(
        langgraph_joke_generator, "ChatAnthropic", _fake_chat_model_factory(response="a joke")
    )

    LangGraphJokeGenerator()

    assert FakeChatModel.instances == []
