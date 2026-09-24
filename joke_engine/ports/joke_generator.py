from typing import Protocol


class JokeGenerationError(Exception):
    """Raised when a JokeGenerator implementation fails to produce a joke."""


class JokeGenerator(Protocol):
    def generate(self, topic: str) -> str:
        """Return joke text about the given topic, or raise JokeGenerationError."""
        ...
