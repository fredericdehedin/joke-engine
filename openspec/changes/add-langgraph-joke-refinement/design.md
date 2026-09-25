# Design

## Context

Today: one-shot `Joke(topic, text)`, `JokeGenerator.generate(topic) -> str`, single ask-then-print CLI run. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- LangGraph stays inside the outbound adapter only.
- `JokeGeneration` is the single source of truth for session history.

**Non-Goals:**
- No cross-run persistence.
- No config or inbound-adapter changes.
- No cap on refinement rounds.

## Flow

```mermaid
flowchart TD
    Topic["User enters topic"] --> Start["CLI calls start(topic)"]
    Start --> UCStart["TellJokeUseCase.start"]
    UCStart --> AdStart["LangGraphJokeGenerator.start"]
    AdStart --> GraphGen["LangGraph node:\nsystem_prompt.txt + topic"]
    GraphGen --> Anthropic1[("Anthropic API")]
    Anthropic1 --> Rev1["JokeGeneration\n(1 revision, style=None)"]
    Rev1 --> Present["CLI presents latest joke"]

    Present --> Choice{"User choice"}
    Choice -->|Accept| Final["Print final joke, exit loop"]
    Choice -->|Quit| Quit["Exit without printing a joke"]
    Choice -->|"Dark & Crude"| RefineDC["refine(generation, DARK_CRUDE)"]
    Choice -->|"Clean & Clever"| RefineCC["refine(generation, CLEAN_CLEVER)"]

    RefineDC --> UCRefine["TellJokeUseCase.refine"]
    RefineCC --> UCRefine
    UCRefine --> AdRefine["LangGraphJokeGenerator.refine"]
    AdRefine --> Lookup["Map RewriteStyle -> resource file\n(dark_crude / clean_clever rewrite prompt)"]
    Lookup --> GraphRewrite["LangGraph node:\nstyle prompt + latest joke text"]
    GraphRewrite --> Anthropic2[("Anthropic API")]
    Anthropic2 --> NewRev["JokeGeneration with new\nRevision appended"]
    NewRev --> Present

    GraphGen -. failure .-> Err["JokeGenerationError"]
    GraphRewrite -. failure .-> Err
    Err --> ErrMsg["CLI prints error message, ends loop"]
```

## Decisions

- **`RewriteStyle` enum** (`DARK_CRUDE`, `CLEAN_CLEVER`) replaces free-text feedback: fixed CLI menu, no arbitrary text reaching the model.
- **`Revision(joke, style)`**: `style` is `None` for the first revision, else the style that produced it.
- **Port**: `start(topic) -> JokeGeneration`, `refine(generation, style: RewriteStyle) -> JokeGeneration`, both raising `JokeGenerationError`.
- **Adapter**: one LangGraph node per call; `refine` picks the system prompt by `RewriteStyle` and sends only the latest joke's text, not the full history.
- **State**: port is stateless per call; no LangGraph checkpointer.
- **Error translation**: same SDK-exception → `JokeGenerationError` pattern as today's adapter.

## Risks / Trade-offs

- New `langgraph` dependency → isolated to the outbound adapter.
- Breaking port change → contained to this change's own touched files.
- No cross-run persistence → acceptable per Non-Goals.
