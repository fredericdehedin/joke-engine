from dotenv import load_dotenv

from joke_engine.adapters.outbound.anthropic_joke_generator import AnthropicJokeGenerator
from joke_engine.application.tell_joke import TellJokeUseCase
from joke_engine.ports.joke_generator import JokeGenerationError


def get_joke_topic() -> str:
    return input("Enter a joke topic: ")


def main() -> None:
    load_dotenv()  # picks up a local .env; never overrides an already-set env var

    joke_topic = get_joke_topic()
    use_case = TellJokeUseCase(AnthropicJokeGenerator())

    try:
        joke = use_case.execute(joke_topic)
    except JokeGenerationError as e:
        print(f"Sorry, I couldn't come up with a joke right now: {e}")
        return

    print(joke.text)


if __name__ == "__main__":
    main()
