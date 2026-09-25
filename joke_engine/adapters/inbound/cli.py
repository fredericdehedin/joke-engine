from dotenv import load_dotenv

from joke_engine.adapters.outbound.langgraph_joke_generator import LangGraphJokeGenerator
from joke_engine.application.tell_joke import TellJokeUseCase
from joke_engine.domain.joke import RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError

STYLE_CHOICES = {
    "d": RewriteStyle.DARK_CRUDE,
    "c": RewriteStyle.CLEAN_CLEVER,
}


REVIEW_PROMPT = (
    "[a] Accept  [d] Rewrite dark & crude  [c] Rewrite clean & clever  [q] Quit\n"
    "Your choice: "
)


def get_joke_topic() -> str | None:
    """Prompt until a non-blank topic is given; None means the user ended input."""
    while True:
        try:
            topic = input("Enter a joke topic: ").strip()
        except EOFError:
            return None
        if topic:
            return topic
        print("Please enter a topic.")


def get_review_choice() -> str:
    try:
        return input(REVIEW_PROMPT).strip().lower()
    except EOFError:
        # No more input (piped stdin, or Ctrl-D): treat it as quitting.
        print()
        return "q"


def show_joke(joke_text: str) -> None:
    print(f"\n{joke_text}\n")


def main() -> None:
    load_dotenv()  # picks up a local .env; never overrides an already-set env var

    joke_topic = get_joke_topic()
    if joke_topic is None:
        return

    use_case = TellJokeUseCase(LangGraphJokeGenerator())

    try:
        generation = use_case.start(joke_topic)
    except JokeGenerationError as e:
        print(f"Sorry, I couldn't come up with a joke right now: {e}")
        return

    show_joke(generation.revisions[-1].joke.text)

    while True:
        choice = get_review_choice()

        if choice in ("a", "q"):
            return

        style = STYLE_CHOICES.get(choice)
        if style is None:
            print("Please choose a, d, c, or q.")
            continue

        try:
            generation = use_case.refine(generation, style)
        except JokeGenerationError as e:
            # Keep the joke the user already has, so a transient failure
            # doesn't end the session.
            print(f"Sorry, I couldn't rewrite that one: {e}")
            continue

        show_joke(generation.revisions[-1].joke.text)


if __name__ == "__main__":
    main()
