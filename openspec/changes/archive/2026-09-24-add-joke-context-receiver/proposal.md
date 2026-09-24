# Proposal

## Why

The joke engine currently has no way to learn what a joke should be about. Before it can generate or tell any joke, it needs a starting interaction that captures a topic ("joke context") from the person running it in the terminal.

## What Changes

- On startup, the terminal app prompts the user to enter a joke context.
- Once the user submits a joke context, the app prints back a confirmation message: `i got the context, i will tell a joke about this: <joke-context>`, using the exact text the user entered.

## Capabilities

### New Capabilities
- `joke-context-intake`: Prompting the user for a joke context on startup and acknowledging the received context by echoing it back in a fixed confirmation format.

### Modified Capabilities
(none)

## Impact

- Affected code: the terminal entry point of the joke engine (currently `hello.py`, a placeholder "Hello, World!" script) becomes the interactive prompt/response loop described above.
- No external dependencies, APIs, or data storage are introduced by this change.
