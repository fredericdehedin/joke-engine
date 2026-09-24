import os
from pathlib import Path

import anthropic

from joke_engine.ports.joke_generator import JokeGenerationError

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_EFFORT = "low"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "resources" / "system_prompt.txt"
SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text().strip()


def resolve_model() -> str:
    return os.environ.get("JOKE_ENGINE_MODEL", DEFAULT_MODEL)


def resolve_effort() -> str:
    return os.environ.get("JOKE_ENGINE_EFFORT", DEFAULT_EFFORT)


def model_supports_effort(model: str) -> bool:
    return "haiku" not in model


class AnthropicJokeGenerator:
    """Outbound adapter implementing the JokeGenerator port via the Anthropic API."""

    def generate(self, topic: str) -> str:
        model = resolve_model()
        request_kwargs = {}
        if model_supports_effort(model):
            request_kwargs["output_config"] = {"effort": resolve_effort()}

        client = anthropic.Anthropic()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Tell me a joke about: {topic}"}],
                **request_kwargs,
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
            # Covers failures the SDK raises before an HTTP call is even made,
            # e.g. no credentials configured at all (raised as a plain TypeError).
            raise JokeGenerationError(str(e)) from e

        return next(block.text for block in response.content if block.type == "text")
