# Tasks

## 1. Implementation

- [x] 1.1 Replace the placeholder `hello.py` entry point with a script that prompts the user for a joke context (e.g. via `input()`) and prints `i got the context, i will tell a joke about this: <joke-context>` using the input verbatim (no trimming or modification); verify by running `python hello.py`, typing "cats", and confirming the printed line matches exactly.
- [x] 1.2 Verify the confirmation message reproduces the entered text verbatim, including leading/trailing whitespace, by running the script with an input like `"  pizza  "` and checking the output is not trimmed.

## 2. Automated Tests

- [x] 2.1 Add `pytest` to the project's dependencies and confirm `pytest` runs (even with zero tests) via `.venv/bin/pip install pytest && .venv/bin/pytest --version`.
- [x] 2.2 Write a test that feeds simulated stdin input ("cats") into the script/function and asserts the exact printed output `i got the context, i will tell a joke about this: cats`; verify with `.venv/bin/pytest`.
- [x] 2.3 Write a test covering the whitespace-preservation scenario from the spec and verify it passes with `.venv/bin/pytest`.
