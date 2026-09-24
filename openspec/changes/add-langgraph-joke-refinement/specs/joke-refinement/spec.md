# Spec Delta

## Purpose

Lets a user iterate on a generated joke for a topic by reviewing it and requesting revisions with feedback, instead of only ever getting the first attempt.

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

### Requirement: Request a revision with feedback
The system SHALL, when the user declines the presented joke and supplies feedback describing what to change, generate a new joke for the same topic that takes that feedback into account, and present the new joke for review in place of the previous one.

#### Scenario: User requests a revision
- **WHEN** the system presents a joke and the user declines it with feedback such as "make it shorter"
- **THEN** the system generates a new joke about the same topic that accounts for that feedback and presents it for review

### Requirement: Repeat review until accepted or stopped
The system SHALL keep presenting revised jokes and requesting accept-or-feedback decisions until the user either accepts a joke or explicitly stops the review loop.

#### Scenario: Multiple rounds of revision
- **WHEN** the user declines two revised jokes in a row with feedback each time
- **THEN** the system generates and presents a new joke after each round of feedback, without limiting the number of revisions

#### Scenario: User stops without accepting
- **WHEN** the system presents a joke and the user explicitly stops the review loop instead of accepting or giving feedback
- **THEN** the system ends the session without displaying any joke as final

### Requirement: Handle joke generation failures during review
The system SHALL, if generating the initial joke or any revision fails for any reason, print a clear, human-readable error message to the terminal instead of an unhandled exception or stack trace, and SHALL end the review loop without presenting that failed attempt as a joke to review or as a final result.

#### Scenario: Initial generation fails
- **WHEN** the user submits a joke topic and generating the initial joke fails
- **THEN** the system prints an error message describing that the joke could not be generated, without a raw stack trace, and does not present a joke for review

#### Scenario: Revision fails after prior joke was already generated
- **WHEN** the user provides feedback to revise a previously presented joke and generating the revision fails
- **THEN** the system prints an error message describing that the revision could not be generated, without a raw stack trace, and does not present a new joke for review
