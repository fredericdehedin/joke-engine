# Design

## Context

The current implementation (clean-architecture layers under `joke_engine/`) has: `domain/joke.py` with a flat `Joke(topic, text)` value object; `ports/joke_generator.py` with a one-shot `JokeGenerator.generate(topic) -> str` Protocol and `JokeGenerationError`; `application/tell_joke.py`'s `TellJokeUseCase.execute(topic) -> Joke`; `adapters/inbound/cli.py`'s single ask-then-print `main()`; and `adapters/outbound/anthropic_joke_generator.py`, which calls the Anthropic SDK directly and translates its exceptions into `JokeGenerationError`. See proposal.md - Why/What Changes for the motivation for moving to a review/refine loop.

## Goals / Non-Goals

**Goals:**
- Keep LangGraph entirely inside a new outbound adapter; `domain`, `ports`, and `application` stay free of any LangGraph/LangChain types.
- Keep the `JokeGeneration` aggregate as the single source of truth for a session's history, rather than relying on LangGraph's own checkpointing for state the rest of the app needs to read.

**Non-Goals:**
- No persistence of `JokeGeneration` across separate CLI runs (in-memory for the duration of one run only).
- No change to `JOKE_ENGINE_MODEL`/`JOKE_ENGINE_EFFORT` configuration behavior - the new adapter reads them the same way the current one does.
- No new inbound adapter - CLI only, same as today.
- No cap on the number of refinement rounds (the spec explicitly requires no limit).

## Decisions

- **`JokeGeneration` shape**: `JokeGeneration(topic: str, revisions: tuple[Revision, ...])` where `Revision(joke: Joke, feedback: str | None)` - `feedback` is `None` for the first revision and holds the feedback that produced each subsequent one. The current joke to display is always `revisions[-1].joke`. Alternative considered: store `topic` and parallel `jokes`/`feedback_history` lists - rejected because pairing each joke with the feedback that produced it in one `Revision` keeps them from drifting out of sync.

- **Port shape**: replace `generate(topic) -> str` with two explicit methods: `start(topic: str) -> JokeGeneration` and `refine(generation: JokeGeneration, feedback: str) -> JokeGeneration`. Both may raise `JokeGenerationError`. Alternative considered: one method taking optional `generation`/`feedback` - rejected because it pushes None-checking branching onto every implementation and caller instead of the port itself expressing the two distinct actions the CLI performs.

- **State ownership**: the port is stateless per call - the caller passes the full `JokeGeneration` into `refine`, and the adapter returns a new one with an appended revision. LangGraph's own checkpointer/thread-based state is not used to hold session history. Alternative considered: let the adapter own state via a LangGraph checkpointer keyed by a thread id, with the port exposing only an opaque session handle - rejected for now, since it would create a second source of truth for history that has to stay correlated with the domain's `JokeGeneration`, for no benefit at this scale (single interactive session, no cross-run persistence goal). Revisit if persistence across runs becomes a goal.

- **LangGraph adapter internals**: a new `adapters/outbound/langgraph_joke_generator.py` implementing the port with a small graph with one node that calls the Anthropic model - the node builds either the initial "write a joke about `<topic>`" prompt or a revision prompt built from the latest joke and the new feedback (e.g. "Here's a joke about `<topic>`: `<latest joke>`. The user said: `<feedback>`. Write a new joke that addresses this."). Only the latest joke + latest feedback are fed into a revision prompt, not the full revision history - keeps prompt size bounded regardless of how many rounds occur, while the full history still lives in `JokeGeneration` for display. `start` and `refine` each run the graph once and map its result back into a new `Revision`.

- **Error translation**: the new adapter keeps the same translation pattern as `anthropic_joke_generator.py` - catch the underlying SDK/LangChain exceptions and re-raise as `JokeGenerationError`, so `cli.py` and `application` keep depending only on the port's error type.

- **Application layer**: `application/tell_joke.py`'s use case is reworked (or replaced) to mirror the port 1:1 - `start(topic)` / `refine(generation, feedback)` - as a thin pass-through. It stays worth keeping as the seam between `cli.py` and the concrete adapter (dependency inversion, mockable in CLI tests) even though it adds little logic beyond delegation today.

- **CLI loop**: `adapters/inbound/cli.py`'s `main()` becomes: read topic, call `start`, then loop presenting `generation.revisions[-1].joke.text` and asking the user to accept, give feedback, or quit; `refine` is called on feedback, the loop exits and prints the final joke on accept, and exits without printing a joke on quit or on a `JokeGenerationError` (per the spec's failure requirements).

- **Testing**: keep the existing fake-based testing style (fake chat model / fake Anthropic client at the same boundary as today) rather than adopting LangGraph's own test utilities, so the new adapter's tests stay consistent with the rest of the suite.

## Risks / Trade-offs

- [New dependency] `langgraph` (plus a LangChain Anthropic integration package) adds weight and a second way of talking to Claude alongside the plain `anthropic` SDK usage elsewhere → mitigated by isolating it entirely inside the new outbound adapter; swapping it out behind the same port later is a contained change.
- [Breaking port change] Existing `JokeGenerator.generate` callers and tests break → contained to this repo's own adapters/application/tests, all of which this change already touches.
- [No persistence across runs] Losing the process loses the whole session → acceptable per Non-Goals; revisit if a "resume a session later" feature is ever wanted.

## Open Questions

- Should the new adapter eventually move to LangGraph's checkpointer/interrupt pattern for human-in-the-loop review, instead of the caller driving `start`/`refine` explicitly? Deferrable - doesn't change the port's external behavior or this change's specs/tasks, only a possible future internal refactor of the adapter.
