# Tasks

## 1. Dependencies

- [ ] 1.1 Add `langgraph` and the LangChain Anthropic integration package to `requirements.txt` and verify `pip install -r requirements.txt` succeeds in a clean virtualenv

## 2. Domain

- [ ] 2.1 Add `RewriteStyle(Enum)` with members `DARK_CRUDE` and `CLEAN_CLEVER`, `Revision(joke: Joke, style: RewriteStyle | None)`, and `JokeGeneration(topic: str, revisions: tuple[Revision, ...])` to `joke_engine/domain/joke.py`, keeping `Joke` as the single revision's value object, and verify with unit tests covering construction and reading the latest revision
- [ ] 2.2 Add validation matching `Joke`'s (non-empty `topic`; `revisions` non-empty; first revision's `style` is `None`; every subsequent revision's `style` is not `None`) and verify with tests for each invalid case

## 3. Ports

- [ ] 3.1 Replace `JokeGenerator.generate(topic) -> str` in `joke_engine/ports/joke_generator.py` with `start(topic: str) -> JokeGeneration` and `refine(generation: JokeGeneration, style: RewriteStyle) -> JokeGeneration`, both documented as raising `JokeGenerationError`, and verify the module imports cleanly with no remaining references to the old method name

## 4. Outbound adapter (LangGraph)

- [ ] 4.1 Create `joke_engine/adapters/outbound/langgraph_joke_generator.py` with a `LangGraphJokeGenerator` implementing the new port, backed by a single-node LangGraph graph that calls the Anthropic model, and verify it satisfies the `JokeGenerator` protocol (e.g. via a type check or protocol-conformance test)
- [ ] 4.2 Implement the initial-generation prompt (reusing `resources/system_prompt.txt`) for `start`, and verify with a test using a fake/stubbed chat model that `start("cats")` returns a `JokeGeneration` with one revision and `style=None`
- [ ] 4.3 Implement a `RewriteStyle -> Path` mapping to `resources/system_prompt_dark_crude_rewrite.txt` and `resources/system_prompt_clean_clever_rewrite.txt`, and use the mapped file's contents as the system prompt for `refine`, sending only the latest joke's text as the user message (not the full history or any free-text feedback), and verify with tests that `refine(generation, RewriteStyle.DARK_CRUDE)` and `refine(generation, RewriteStyle.CLEAN_CLEVER)` each append a new `Revision` with the matching `style` and invoke the fake model with the corresponding resource file's system prompt and the latest joke's text
- [ ] 4.4 Wrap the graph invocation in `start`/`refine` with the same most-specific-first exception translation to `JokeGenerationError` used in `anthropic_joke_generator.py`, and verify with tests that simulated SDK/LangChain failures during `start` and during `refine` both raise `JokeGenerationError` with a human-readable message
- [ ] 4.5 Verify `resolve_model`/`resolve_effort`/`model_supports_effort` behavior (env var defaults and overrides) is preserved in the new adapter, with tests mirroring the existing `anthropic_joke_generator` coverage

## 5. Application

- [ ] 5.1 Rework `joke_engine/application/tell_joke.py` into a use case matching the new port (`start(topic) -> JokeGeneration`, `refine(generation, style: RewriteStyle) -> JokeGeneration`) that delegates to the injected `JokeGenerator`, and verify with tests using a fake `JokeGenerator` that both methods delegate correctly and propagate `JokeGenerationError`

## 6. Inbound CLI

- [ ] 6.1 Change `joke_engine/adapters/inbound/cli.py`'s `main()` to call `start(topic)`, then loop: display `generation.revisions[-1].joke.text`, prompt the user to accept, pick a rewrite style ("dark & crude" / "clean & clever"), or quit, and verify with a test (fake input sequence + fake generator) that accepting on the first round prints that joke and exits the loop
- [ ] 6.2 Wire each style pick to call `refine(generation, style)` with the matching `RewriteStyle` member and loop back to display the new joke, and verify with a test that picking a style then accepting results in the second (revised) joke being the one printed, with no cap on the number of rounds
- [ ] 6.3 Wire the quit path to end the session without printing any joke as final, and verify with a test asserting no joke text appears in output when the user quits immediately
- [ ] 6.4 Wire `JokeGenerationError` handling for both the initial `start` call and any `refine` call to print the existing "Sorry, I couldn't come up with a joke right now: ..." message and end the loop, and verify with tests covering a failure on `start` and a failure on `refine` after one accepted style pick

## 7. Cleanup and full-suite verification

- [ ] 7.1 Remove `joke_engine/adapters/outbound/anthropic_joke_generator.py` and its tests, since `LangGraphJokeGenerator` fully replaces it, and verify no remaining imports reference the removed module
- [ ] 7.2 Run the full test suite (`pytest`) and verify all tests pass with no real network calls made
