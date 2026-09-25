from dotenv import load_dotenv

from joke_engine.adapters.outbound.langgraph_joke_generator import LangGraphJokeGenerator
from joke_engine.application.tell_joke import TellJokeUseCase
from joke_engine.domain.joke import RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerationError

STYLE_CHOICES = {
    "d": RewriteStyle.DARK_CRUDE,
    "c": RewriteStyle.CLEAN_CLEVER,
}


def get_joke_topic() -> str:
    return input("Enter a joke topic: ")


def get_review_choice(joke_text: str) -> str:
    prompt = (
        f"\n{joke_text}\n\n"
        "[a] Accept  [d] Rewrite dark & crude  [c] Rewrite clean & clever  [q] Quit\n"
        "Your choice: "
    )
    return input(prompt).strip().lower()


def main() -> None:
    load_dotenv()  # picks up a local .env; never overrides an already-set env var

    joke_topic = get_joke_topic()
    use_case = TellJokeUseCase(LangGraphJokeGenerator())

    try:
        generation = use_case.start(joke_topic)
    except JokeGenerationError as e:
        print(f"Sorry, I couldn't come up with a joke right now: {e}")
        return

    while True:
        choice = get_review_choice(generation.revisions[-1].joke.text)

        if choice == "a":
            print(generation.revisions[-1].joke.text)
            return
        if choice == "q":
            return

        style = STYLE_CHOICES.get(choice)
        if style is None:
            print("Please choose a, d, c, or q.")
            continue

        try:
            generation = use_case.refine(generation, style)
        except JokeGenerationError as e:
            print(f"Sorry, I couldn't come up with a joke right now: {e}")
            return


if __name__ == "__main__":
    main()
