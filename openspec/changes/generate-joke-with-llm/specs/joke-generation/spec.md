# Spec Delta

## Purpose

Turns a user-supplied joke topic into an actual joke by asking Claude (via the Anthropic API) to write one about that topic, and shows the result in the terminal.

## ADDED Requirements

### Requirement: Generate a joke about the given topic
The system SHALL, after receiving the user's joke topic, call the Anthropic API with a request for a joke about that topic and use the joke text from the response for display.

#### Scenario: Topic submitted successfully
- **WHEN** the user enters "cats" as the joke topic and submits it
- **THEN** the system sends a request to the Anthropic API asking for a joke about "cats"

### Requirement: Display the generated joke
The system SHALL print the joke text returned by the Anthropic API to the terminal.

#### Scenario: API call succeeds
- **WHEN** the Anthropic API returns a joke about the submitted topic
- **THEN** the system prints that joke's text to the terminal

### Requirement: Handle joke generation failures
The system SHALL, if the Anthropic API call fails for any reason (missing or invalid API key, network error, rate limiting, or any other error), print a clear, human-readable error message to the terminal instead of an unhandled exception/stack trace, and SHALL NOT print a joke in that case.

#### Scenario: API key is missing or invalid
- **WHEN** the user submits a joke topic and the Anthropic API call fails due to an authentication error
- **THEN** the system prints an error message describing that the joke could not be generated, without a raw stack trace

#### Scenario: Network or server error
- **WHEN** the user submits a joke topic and the Anthropic API call fails due to a network error or server-side error
- **THEN** the system prints an error message describing that the joke could not be generated, without a raw stack trace

### Requirement: Configurable model via environment variable
The system SHALL read the model used for joke generation from the `JOKE_ENGINE_MODEL` environment variable, and SHALL default to `claude-haiku-4-5` (the most cost-efficient available model) when that variable is unset.

#### Scenario: No model override set
- **WHEN** the user runs the app without setting `JOKE_ENGINE_MODEL`
- **THEN** the system requests a joke using model `claude-haiku-4-5`

#### Scenario: Model override set
- **WHEN** the user runs the app with `JOKE_ENGINE_MODEL` set to a different model id
- **THEN** the system requests a joke using that configured model id

### Requirement: Configurable effort via environment variable
The system SHALL read the effort level for joke generation from the `JOKE_ENGINE_EFFORT` environment variable, and SHALL default to `low` (the most cost-efficient effort level) when that variable is unset. The system SHALL only include the effort setting in the request to the Anthropic API when the configured model supports the `effort` parameter, and SHALL omit it otherwise so the request does not fail on a model that rejects it.

#### Scenario: Default model and effort (most cost-efficient)
- **WHEN** the user runs the app without setting `JOKE_ENGINE_MODEL` or `JOKE_ENGINE_EFFORT`
- **THEN** the system requests a joke using model `claude-haiku-4-5` without an effort setting, since that model does not support the `effort` parameter

#### Scenario: Effort override on a model that supports it
- **WHEN** the user sets `JOKE_ENGINE_MODEL` to a model that supports the `effort` parameter and sets `JOKE_ENGINE_EFFORT` to a valid effort level
- **THEN** the system requests a joke using that model with the configured effort level applied

### Requirement: Load configuration from a local .env file
The system SHALL, on startup, load `ANTHROPIC_API_KEY`, `JOKE_ENGINE_MODEL`, and `JOKE_ENGINE_EFFORT` from a local `.env` file if one is present, without overriding any of those variables that are already set in the environment. The system SHALL run normally when no `.env` file is present.

#### Scenario: Value provided only via .env
- **WHEN** a `.env` file in the working directory sets `ANTHROPIC_API_KEY` and no such environment variable is already set
- **THEN** the system uses the value from `.env` for the Anthropic API call

#### Scenario: Environment variable takes precedence over .env
- **WHEN** `JOKE_ENGINE_MODEL` is already set in the environment and a `.env` file in the working directory also sets `JOKE_ENGINE_MODEL` to a different value
- **THEN** the system uses the value already set in the environment, not the value from `.env`

#### Scenario: No .env file present
- **WHEN** no `.env` file exists in the working directory
- **THEN** the system runs normally, resolving configuration from environment variables and defaults as usual
