# Tasks

## 1. Dependencies

- [x] 1.1 Add `anthropic` to `requirements.txt` and verify it installs cleanly via `.venv/bin/pip install -r requirements.txt`.

## 2. Joke Generation

- [x] 2.1 In `tell_me_a_joke.py`, add a function that reads `JOKE_ENGINE_MODEL` (default `claude-haiku-4-5`) and `JOKE_ENGINE_EFFORT` (default `low`) from the environment, and a small check (e.g. a set/prefix check for Haiku models) for whether the configured model supports the `effort` parameter; verify by inspecting the function with both env vars unset and confirming it resolves to `claude-haiku-4-5` / effort-not-applied.
- [x] 2.2 Add a function that takes the joke topic, calls `anthropic.Anthropic().messages.create(...)` with the resolved model, a system prompt instructing a joke-only response, a user message naming the topic, and `output_config={"effort": ...}` included only when the model-supports-effort check from 2.1 passes; returns the joke text from the first `text` content block. Verify by manually running the script with `ANTHROPIC_API_KEY` set and a topic like "cats", confirming a joke is printed instead of the old echo line.
- [x] 2.3 Update `main()` to call this function with the submitted topic and print the returned joke text, removing the old `i got the topic, i will tell a joke about this: <topic>` echo.
- [x] 2.4 Wrap the API call in a most-specific-first `except` chain (`anthropic.AuthenticationError`, `anthropic.RateLimitError`, `anthropic.APIStatusError`, `anthropic.APIConnectionError`) that prints a short, human-readable error message and does not print a joke; verify manually by running with an invalid/unset `ANTHROPIC_API_KEY` and confirming a clean error message (no stack trace) is printed.

## 3. Automated Tests

- [x] 3.1 Replace the two tests in `tests/test_tell_me_a_joke.py` that assert the old echo string with tests that mock the Anthropic client/API call and assert the joke text it returns is printed to the terminal; verify with `.venv/bin/pytest`.
- [x] 3.2 Add a test that simulates an Anthropic API error (e.g. mock `messages.create` to raise `anthropic.APIConnectionError`) and asserts a clean error message is printed and no joke text appears in the output; verify with `.venv/bin/pytest`.
- [x] 3.3 Add tests for the env var resolution: (a) with `JOKE_ENGINE_MODEL`/`JOKE_ENGINE_EFFORT` unset, the API call is made with model `claude-haiku-4-5` and no `effort` in `output_config`; (b) with `JOKE_ENGINE_MODEL` set to a model that supports `effort` and `JOKE_ENGINE_EFFORT` set to a valid value, the API call includes that model and effort; verify with `.venv/bin/pytest`.

## 4. Local .env Support

- [x] 4.1 Add `python-dotenv` to `requirements.txt` and verify it installs cleanly via `.venv/bin/pip install -r requirements.txt`.
- [x] 4.2 Add `.env` to `.gitignore` and verify with `git status` that a locally created `.env` file does not show up as trackable/untracked-for-commit.
- [x] 4.3 Call `load_dotenv()` (from `python-dotenv`) once at the top of `main()` in `tell_me_a_joke.py`, before resolving any configuration; verify by creating a local `.env` with `JOKE_ENGINE_MODEL=claude-haiku-4-5` (no env var set) and confirming the app picks it up.
- [x] 4.4 Create a local `.env` file (gitignored, not committed) with placeholder entries for `ANTHROPIC_API_KEY`, `JOKE_ENGINE_MODEL`, and `JOKE_ENGINE_EFFORT` for the user to fill in with a real key.
- [x] 4.5 Add a test that creates a temporary `.env`-style file (e.g. via `monkeypatch.chdir` to a tmp dir with a `.env` file, or by calling `load_dotenv` against a temp path) and asserts a value set only in `.env` is picked up, and that a value already set in the environment takes precedence over `.env`; verify with `.venv/bin/pytest`.
- [x] 4.6 Add a committed `.env-template` file at the repo root with instructions to copy it to `.env` and fill in `ANTHROPIC_API_KEY`, and with `JOKE_ENGINE_MODEL`/`JOKE_ENGINE_EFFORT` pre-filled with the existing cost-efficient defaults; verify it is not matched by the `.env` gitignore rule (`git check-ignore -v .env-template` reports no match) and shows up as trackable via `git status`.
