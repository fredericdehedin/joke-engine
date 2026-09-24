# Proposal

## Why

The joke engine currently just echoes the user's topic back (`i got the topic, i will tell a joke about this: <topic>`) instead of actually telling a joke. The user now has an Anthropic API key available, so the app can call Claude to generate a real joke about the given topic and display it in the terminal.

## What Changes

- After the user enters a joke topic, the app calls the Anthropic API (Claude) with a prompt asking for a joke about that topic, instead of just echoing the topic back.
- The app prints the joke text returned by the API to the terminal.
- If the API call fails (missing/invalid API key, network error, rate limit, etc.), the app prints a clear error message to the terminal instead of crashing with a raw traceback.
- The model and effort level used for joke generation are configurable via environment variables (`JOKE_ENGINE_MODEL`, `JOKE_ENGINE_EFFORT`), defaulting to the most cost-efficient combination available (`claude-haiku-4-5`, effort `low`).
- `ANTHROPIC_API_KEY`, `JOKE_ENGINE_MODEL`, and `JOKE_ENGINE_EFFORT` can also be set in a local `.env` file, which the app loads automatically on startup; a value already set in the environment still takes precedence over `.env`.
- **BREAKING**: The terminal output no longer contains the literal echo line `i got the topic, i will tell a joke about this: <topic>`; it is replaced by the generated joke text.

## Capabilities

### New Capabilities
- `joke-generation`: Given a joke topic, calling the Anthropic API to generate a joke about that topic and displaying the resulting joke (or a clear error message on failure) in the terminal.

### Modified Capabilities
(none - no existing capability is captured in `openspec/specs/`; topic intake behavior itself is unchanged, only what happens after intake)

## Impact

- Affected code: `tell_me_a_joke.py` - the `main()` function's post-intake behavior changes from printing a fixed echo string to calling the Anthropic API and printing its response.
- New dependency: `anthropic` Python SDK (added to `requirements.txt`).
- New runtime requirement: a valid `ANTHROPIC_API_KEY` environment variable must be set for the app to generate jokes.
- New optional runtime configuration: `JOKE_ENGINE_MODEL` and `JOKE_ENGINE_EFFORT` environment variables, defaulting to the cheapest model (`claude-haiku-4-5`) and effort `low`. Effort is only sent to the API when the configured model supports the `effort` parameter (Haiku 4.5 does not; the API rejects it there), so it is a no-op at the default settings and only takes effect if `JOKE_ENGINE_MODEL` is overridden to a model that supports it.
- Tests: existing tests asserting the old echo message (`tests/test_tell_me_a_joke.py`) will need to be replaced with tests that mock the Anthropic API call.
- `.env` is a local, untracked file - it must be added to `.gitignore` and must never be committed, since it can hold a real `ANTHROPIC_API_KEY`.
