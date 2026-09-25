# Spec Delta

## Purpose

Lets a user iterate on a generated joke for a topic by reviewing it and requesting a rewrite in a chosen style, instead of only ever getting the first attempt.

## ADDED Requirements

### Requirement: Generate an initial joke for review
The system SHALL, after receiving the user's joke topic, generate a joke about that topic and present it to the user for review before treating it as final.

#### Scenario: Topic submitted successfully
- **WHEN** the user enters "cats" as the joke topic and submits it
- **THEN** the system generates a joke about "cats" and presents it to the user for review

### Requirement: Accept the presented joke
The system SHALL, when the user accepts the presented joke, treat it as final, display it, and end the review loop without asking for further feedback.

#### Scenario: User accepts the first joke
- **WHEN** the system presents a joke and the user accepts it
- **THEN** the system displays that joke as the final result and does not ask for further feedback

### Requirement: Request a revision in a chosen rewrite style
The system SHALL, when the user declines the presented joke, offer exactly two rewrite styles - "dark & crude" and "clean & clever" - and, once the user picks one, generate a new joke that rewrites the presented joke in that style while keeping the same topic, then present the new joke for review in place of the previous one.

#### Scenario: User requests a dark & crude rewrite
- **WHEN** the system presents a joke and the user declines it and picks the "dark & crude" style
- **THEN** the system generates a new joke about the same topic rewritten in a darker, cruder tone and presents it for review

#### Scenario: User requests a clean & clever rewrite
- **WHEN** the system presents a joke and the user declines it and picks the "clean & clever" style
- **THEN** the system generates a new joke about the same topic rewritten in a cleaner, more clever tone and presents it for review

### Requirement: Repeat review until accepted or stopped
The system SHALL keep presenting rewritten jokes and requesting accept-or-choose-a-style decisions until the user either accepts a joke or explicitly stops the review loop.

#### Scenario: Multiple rounds of revision
- **WHEN** the user declines two rewritten jokes in a row, picking a rewrite style each time
- **THEN** the system generates and presents a new joke after each style pick, without limiting the number of revisions

#### Scenario: User stops without accepting
- **WHEN** the system presents a joke and the user explicitly stops the review loop instead of accepting or picking a rewrite style
- **THEN** the system ends the session without displaying any joke as final

### Requirement: Handle joke generation failures during review
The system SHALL, if generating the initial joke or any revision fails for any reason, print a clear, human-readable error message to the terminal instead of an unhandled exception or stack trace, and SHALL end the review loop without presenting that failed attempt as a joke to review or as a final result.

#### Scenario: Initial generation fails
- **WHEN** the user submits a joke topic and generating the initial joke fails
- **THEN** the system prints an error message describing that the joke could not be generated, without a raw stack trace, and does not present a joke for review

#### Scenario: Revision fails after prior joke was already generated
- **WHEN** the user picks a rewrite style to revise a previously presented joke and generating the revision fails
- **THEN** the system prints an error message describing that the revision could not be generated, without a raw stack trace, and does not present a new joke for review
