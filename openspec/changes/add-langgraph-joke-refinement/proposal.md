# Proposal

## Why

Today's joke generation is one-shot: the user submits a topic, gets a single joke, and the program exits. If the joke misses (wrong tone, not funny, off-topic), the only recourse is running the whole CLI again with the same topic and hoping for a better roll. Letting the user give feedback and get a revised joke, without restarting, makes the tool meaningfully more useful, and LangGraph is a natural fit for orchestrating that multi-step, stateful generate/revise loop.

## What Changes

- Introduce a `JokeGeneration` domain aggregate: a topic plus an ordered history of `Joke` revisions, each optionally tied to the user feedback that produced it. The existing flat `Joke(topic, text)` value object becomes the single revision entry inside that history.
- **BREAKING**: Replace the one-shot `JokeGenerator.generate(topic) -> str` port with a session-shaped port, e.g. `start(topic) -> JokeGeneration` and `refine(generation, feedback) -> JokeGeneration`. Existing implementations/tests against the old port signature no longer apply.
- Add a new outbound adapter that implements the port using LangGraph to orchestrate the Anthropic calls for both the initial generation and each refinement step. LangGraph's graph/node/checkpoint concepts stay entirely inside this adapter - `domain`, `ports`, and `application` never reference LangGraph.
- Change `adapters/inbound/cli.py` from "ask once, print once" to an interactive loop: show the current joke, ask the user whether to keep it or provide feedback to refine it, repeat until the user accepts (or quits).
- Add `langgraph` (and any Anthropic/LangChain integration package it requires) to `requirements.txt`.

## Capabilities

### New Capabilities
- `joke-refinement`: the user-driven loop of generating a joke for a topic, reviewing it, and requesting revisions with feedback until satisfied, orchestrated via LangGraph.

### Modified Capabilities
<!-- none: the existing single-shot generation behavior (still an open, unarchived change - generate-joke-with-llm) is being superseded/extended by joke-refinement rather than edited in place, since its spec has not yet landed under openspec/specs/. -->

## Impact

- `joke_engine/ports/joke_generator.py`: port signature changes from single-shot `generate` to session-shaped `start`/`refine`.
- `joke_engine/domain/joke.py`: new `JokeGeneration` aggregate alongside the existing `Joke` value object.
- `joke_engine/adapters/outbound/`: new LangGraph-backed adapter (replacing or sitting alongside `anthropic_joke_generator.py`); the prior direct one-shot `messages.create` call is superseded by graph-orchestrated calls.
- `joke_engine/adapters/inbound/cli.py`: interactive accept/refine loop instead of a single request/response.
- `joke_engine/application/tell_joke.py`: use case reworked around the new port shape (or replaced by a use case matching `start`/`refine`).
- `requirements.txt`: add `langgraph` and its required Anthropic/LangChain integration dependency.
- Tests under `tests/adapters/outbound/`, `tests/adapters/inbound/`, and `tests/application/` need rewriting against the new port and CLI loop.
