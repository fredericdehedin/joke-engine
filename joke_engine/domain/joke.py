from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Joke:
    topic: str
    text: str

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")


class RewriteStyle(Enum):
    DARK_CRUDE = "dark_crude"
    CLEAN_CLEVER = "clean_clever"


@dataclass(frozen=True)
class Revision:
    joke: Joke
    style: RewriteStyle | None


@dataclass(frozen=True)
class JokeGeneration:
    topic: str
    revisions: tuple[Revision, ...]

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not self.revisions:
            raise ValueError("revisions must not be empty")
        if self.revisions[0].style is not None:
            raise ValueError("first revision's style must be None")
        if any(revision.style is None for revision in self.revisions[1:]):
            raise ValueError("every revision after the first must have a style")
