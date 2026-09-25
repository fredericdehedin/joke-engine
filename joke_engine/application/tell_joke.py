from joke_engine.domain.joke import JokeGeneration, RewriteStyle
from joke_engine.ports.joke_generator import JokeGenerator


class TellJokeUseCase:
    def __init__(self, joke_generator: JokeGenerator) -> None:
        self._joke_generator = joke_generator

    def start(self, topic: str) -> JokeGeneration:
        return self._joke_generator.start(topic)

    def refine(self, generation: JokeGeneration, style: RewriteStyle) -> JokeGeneration:
        return self._joke_generator.refine(generation, style)
