# Design

## Context

`tell_me_a_joke.py` currently has `get_joke_topic()` (reads a topic via `input()`) and `main()` (prints a fixed echo string using that topic). See proposal.md - Why/What Changes for the motivation. The user has an `ANTHROPIC_API_KEY` available in their environment. The project already depends on `pytest` for tests (`requirements.txt`); no HTTP or LLM client library is present yet.

## Goals / Non-Goals

**Goals:**
- Replace the echo behavior with a real call to the Anthropic API that generates a joke about the submitted topic, and print that joke.
- Fail gracefully (readable message, non-zero-drama exit) when the API call cannot succeed, rather than surfacing a raw exception.

**Non-Goals:**
- No streaming output, multi-turn conversation, or joke history/caching - this is a single request/response per run.
- No CLI flags or config file for choosing model/effort/prompt/output format - environment variables only (`JOKE_ENGINE_MODEL`, `JOKE_ENGINE_EFFORT`).
- No validation of unknown/invalid model ids passed via `JOKE_ENGINE_MODEL` beyond letting the Anthropic API reject them - errors surface through the existing error-handling requirement.
- No retry/backoff logic beyond what the Anthropic SDK already does by default.

## Decisions

- **Use the official `anthropic` Python SDK**, not raw HTTP - this is a Python project and the SDK is the default per project convention for talking to the Anthropic API. Add `anthropic` to `requirements.txt`.
- **Client construction**: `anthropic.Anthropic()` with no explicit `api_key` argument, so it resolves `ANTHROPIC_API_KEY` (or another configured credential source) from the environment. Nothing is hardcoded and no new config file is introduced.
- **Model**: read from `JOKE_ENGINE_MODEL`, defaulting to `claude-haiku-4-5` - the cheapest current model ($1/$5 per 1M tokens) and more than capable of writing a short joke. Non-streaming `client.messages.create(...)` call; the output is a single short joke, well under any timeout concern, so streaming isn't needed.
- **Effort**: read from `JOKE_ENGINE_EFFORT`, defaulting to `low` - the cheapest effort level, for when the configured model supports it. Claude Haiku 4.5 (the default model) does not accept `output_config.effort` at all - the API rejects the request if it's sent - so the app only includes `output_config.effort` in the request when the configured model is known to support it (i.e. not a Haiku model); it is a no-op at the default settings and only takes effect once `JOKE_ENGINE_MODEL` is overridden to a model that supports it (Sonnet/Opus/Fable tiers). Alternative considered: always send `effort` and let unsupported combinations error - rejected because it would make the cost-efficient default (Haiku) fail on every run, defeating the point of defaulting to it.
- **Prompt shape**: a short system prompt instructing Claude to respond with only the joke (no preamble/commentary), and a user message asking for a joke about the submitted topic. `max_tokens` set to a small fixed value (e.g. 512) since jokes are short.
- **Extracting the joke text**: iterate `response.content` for the first block with `type == "text"` and print its `.text`, matching the pattern already used elsewhere for reading Claude responses.
- **Error handling**: wrap the API call in a most-specific-first `except` chain over the SDK's typed exceptions (`anthropic.AuthenticationError`, `anthropic.RateLimitError`, `anthropic.APIStatusError`, `anthropic.APIConnectionError`), each printing a short, user-facing message (e.g. `"Sorry, I couldn't come up with a joke right now: <reason>"`) instead of letting the exception propagate. This is an external-API boundary, so validating/handling failure here is warranted (unlike input validation elsewhere in the app, which stays untouched). A final `except Exception` catch-all follows the typed chain: with no credentials configured at all, the SDK raises a plain `TypeError` during request-header validation before any HTTP call is made, not one of its typed exceptions - the spec's "for any reason... SHALL NOT print a stack trace" requirement covers this case too, so it needs a fallback handler.
- **Loading `.env`**: use `python-dotenv`'s `load_dotenv()`, called once at the top of `main()`, rather than hand-rolling a parser - it's the standard tool for this and its default behavior already matches the spec (it does not override a variable that's already set in the environment, and is a no-op when no `.env` file exists). Add `python-dotenv` to `requirements.txt`. Add `.env` to `.gitignore` - it must never be committed, since it can hold a real `ANTHROPIC_API_KEY`.
- **`.env-template`**: a committed file (not gitignored) with setup instructions and `JOKE_ENGINE_MODEL`/`JOKE_ENGINE_EFFORT` pre-filled with the existing cost-efficient defaults, and an empty `ANTHROPIC_API_KEY` for the user to fill in after copying it to `.env`. This is the checked-in counterpart to the gitignored `.env` - it documents the required setup without holding any secret.
- **Testing**: mock the Anthropic client (e.g. `monkeypatch` on the function that constructs the client, or on `client.messages.create`) so tests don't make real network calls or require a real API key. Replace the two existing tests in `tests/test_tell_me_a_joke.py` that assert the old echo string, since that output no longer exists. Cover the `JOKE_ENGINE_MODEL`/`JOKE_ENGINE_EFFORT` default and override behavior, including that `effort` is omitted for the default Haiku model and included when a supporting model is configured.

## Risks / Trade-offs

- [API latency/availability] Every run now depends on a live network call to Anthropic → mitigated by the error-handling requirement (Requirement: Handle joke generation failures) so a failure degrades to a clear message rather than a crash.
- [Cost] Every run now costs real API tokens, however small → minimized by defaulting to the cheapest model and effort level; still acceptable at any setting since this is a personal CLI tool run interactively by the user, not a high-volume service.
- [No API key set] Running the app without `ANTHROPIC_API_KEY` configured will hit the authentication-error path on every run → acceptable per Non-Goals; the error message should make the missing-key case understandable without adding key-setup UX to this change.
- [Model/effort mismatch] Setting `JOKE_ENGINE_MODEL` to a model that doesn't support `effort` together with a non-default `JOKE_ENGINE_EFFORT` could otherwise cause every request to fail → mitigated by only sending `output_config.effort` when the configured model is known to support it, per the Effort decision above.
