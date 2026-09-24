# Spec Delta

## Purpose

Captures the topic a joke should be about by prompting the user for a joke context when the terminal app starts, and confirms receipt before any joke is generated.

## ADDED Requirements

### Requirement: Prompt for joke context on startup
The system SHALL prompt the user to enter a joke context when the terminal application starts.

#### Scenario: App starts and waits for input
- **WHEN** the terminal application is launched
- **THEN** the system displays a prompt requesting the user to enter a joke context and waits for input

### Requirement: Acknowledge received joke context
The system SHALL, upon receiving the user's joke context input, print a confirmation message in the exact form `i got the context, i will tell a joke about this: <joke-context>`, where `<joke-context>` is replaced verbatim with the text the user entered.

#### Scenario: User enters a joke context
- **WHEN** the user enters "cats" as the joke context and submits it
- **THEN** the system prints "i got the context, i will tell a joke about this: cats"

#### Scenario: User enters a joke context containing extra whitespace
- **WHEN** the user enters "  pizza  " as the joke context and submits it
- **THEN** the system prints "i got the context, i will tell a joke about this:   pizza  " reproducing the entered text verbatim
