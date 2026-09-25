import os
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

import anthropic
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from joke_engine.domain.joke import Joke, JokeGeneration, Revision, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_EFFORT = "low"
RESOURCES_DIR = Path(__file__).parent / "resources"
SYSTEM_PROMPT = (RESOURCES_DIR / "system_prompt.txt").read_text().strip()
REWRITE_SYSTEM_PROMPTS = {
    RewriteStyle.DARK_CRUDE: (RESOURCES_DIR / "system_prompt_dark_crude_rewrite.txt").read_text().strip(),
    RewriteStyle.CLEAN_CLEVER: (RESOURCES_DIR / "system_prompt_clean_clever_rewrite.txt").read_text().strip(),
}


def resolve_model() -> str:
    return os.environ.get("JOKE_ENGINE_MODEL", DEFAULT_MODEL)


def resolve_effort() -> str:
    return os.environ.get("JOKE_ENGINE_EFFORT", DEFAULT_EFFORT)


def model_supports_effort(model: str) -> bool:
    return "haiku" not in model


class _GraphState(TypedDict):
    system_prompt: str
    user_message: str
    joke_text: str


def _extract_text(content) -> str:
    """Join the text blocks of a response.

    langchain_anthropic only sets ``content`` to a plain string when the reply
    holds exactly one text block; with thinking enabled (which `output_config`
    turns on) it is a list of blocks instead.
    """
    if isinstance(content, str):
        return content

    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
        elif getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts)


@contextmanager
def _as_generation_error():
    """Translate domain validation failures into the port's error type.

    A reply that is empty or whitespace-only -- a truncated response, or one
    the model filtered -- must reach callers as a JokeGenerationError like any
    other failure, not as a raw ValueError.
    """
    try:
        yield
    except ValueError as e:
        raise JokeGenerationError(f"the model returned an unusable joke: {e}") from e


def _generate(state: _GraphState) -> dict:
    model = resolve_model()
    model_kwargs = {}
    if model_supports_effort(model):
        model_kwargs["output_config"] = {"effort": resolve_effort()}

    chat_model = ChatAnthropic(model=model, max_tokens=512, **model_kwargs)
    response = chat_model.invoke(
        [
            SystemMessage(content=state["system_prompt"]),
            HumanMessage(content=state["user_message"]),
        ]
    )
    return {"joke_text": _extract_text(response.content)}


def _build_graph():
    graph = StateGraph(_GraphState)
    graph.add_node("generate", _generate)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", END)
    return graph.compile()


class LangGraphJokeGenerator:
    """Outbound adapter implementing the JokeGenerator port via LangGraph + Anthropic."""

    def __init__(self) -> None:
        self._graph = _build_graph()

    def start(self, topic: str) -> JokeGeneration:
        joke_text = self._run(SYSTEM_PROMPT, f"Tell me a joke about: {topic}")
        with _as_generation_error():
            joke = Joke(topic=topic, text=joke_text)
            return JokeGeneration(topic=topic, revisions=(Revision(joke=joke, style=None),))

    def refine(self, generation: JokeGeneration, style: RewriteStyle) -> JokeGeneration:
        latest_joke = generation.revisions[-1].joke
        joke_text = self._run(REWRITE_SYSTEM_PROMPTS[style], latest_joke.text)
        with _as_generation_error():
            joke = Joke(topic=generation.topic, text=joke_text)
            return JokeGeneration(
                topic=generation.topic,
                revisions=generation.revisions + (Revision(joke=joke, style=style),),
            )

    def _run(self, system_prompt: str, user_message: str) -> str:
        try:
            result = self._graph.invoke(
                {"system_prompt": system_prompt, "user_message": user_message, "joke_text": ""}
            )
        except anthropic.AuthenticationError as e:
            raise JokeGenerationError("invalid or missing API key.") from e
        except anthropic.RateLimitError as e:
            raise JokeGenerationError("rate limited, try again later.") from e
        except anthropic.APIStatusError as e:
            raise JokeGenerationError(e.message) from e
        except anthropic.APIConnectionError as e:
            raise JokeGenerationError("network error.") from e
        except Exception as e:
            # Covers failures raised before an HTTP call is even made,
            # e.g. no credentials configured at all.
            raise JokeGenerationError(str(e)) from e

        return result["joke_text"]
