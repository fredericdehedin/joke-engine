from typing import Protocol, runtime_checkable

from joke_engine.domain.joke import JokeGeneration, RewriteStyle


class JokeGenerationError(Exception):
    """Raised when a JokeGenerator implementation fails to produce a joke."""


@runtime_checkable
class JokeGenerator(Protocol):
    def start(self, topic: str) -> JokeGeneration:
        """Return a JokeGeneration with one initial revision, or raise JokeGenerationError."""
        ...

    def refine(self, generation: JokeGeneration, style: RewriteStyle) -> JokeGeneration:
        """Return a new JokeGeneration with a revision rewritten in the given style, or raise JokeGenerationError."""
        ...
