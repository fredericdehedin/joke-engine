#!/usr/bin/env python3

import os

import anthropic
from dotenv import load_dotenv

DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_EFFORT = "low"


def get_joke_topic() -> str:
    return input("Enter a joke topic: ")


def resolve_model() -> str:
    return os.environ.get("JOKE_ENGINE_MODEL", DEFAULT_MODEL)


def resolve_effort() -> str:
    return os.environ.get("JOKE_ENGINE_EFFORT", DEFAULT_EFFORT)


def model_supports_effort(model: str) -> bool:
    return "haiku" not in model


def generate_joke(topic: str) -> str:
    model = resolve_model()
    request_kwargs = {}
    if model_supports_effort(model):
        request_kwargs["output_config"] = {"effort": resolve_effort()}

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=512,
        system=(
            "You are a comedian. Respond with only a short joke about the "
            "given topic. No preamble or commentary."
        ),
        messages=[{"role": "user", "content": f"Tell me a joke about: {topic}"}],
        **request_kwargs,
    )

    return next(block.text for block in response.content if block.type == "text")


def main() -> None:
    load_dotenv()  # picks up a local .env; never overrides an already-set env var

    joke_topic = get_joke_topic()

    try:
        joke = generate_joke(joke_topic)
    except anthropic.AuthenticationError:
        print("Sorry, I couldn't come up with a joke right now: invalid or missing API key.")
        return
    except anthropic.RateLimitError:
        print("Sorry, I couldn't come up with a joke right now: rate limited, try again later.")
        return
    except anthropic.APIStatusError as e:
        print(f"Sorry, I couldn't come up with a joke right now: {e.message}")
        return
    except anthropic.APIConnectionError:
        print("Sorry, I couldn't come up with a joke right now: network error.")
        return
    except Exception as e:
        # Covers failures the SDK raises before an HTTP call is even made,
        # e.g. no credentials configured at all (raised as a plain TypeError).
        print(f"Sorry, I couldn't come up with a joke right now: {e}")
        return

    print(joke)


if __name__ == "__main__":
    main()
