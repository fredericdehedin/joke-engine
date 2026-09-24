from joke_engine.domain.joke import Joke
from joke_engine.ports.joke_generator import JokeGenerator


class TellJokeUseCase:
    def __init__(self, joke_generator: JokeGenerator) -> None:
        self._joke_generator = joke_generator

    def execute(self, topic: str) -> Joke:
        text = self._joke_generator.generate(topic)
        return Joke(topic=topic, text=text)
