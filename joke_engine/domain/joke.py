from dataclasses import dataclass


@dataclass(frozen=True)
class Joke:
    topic: str
    text: str

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")
