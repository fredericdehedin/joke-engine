# Joke Engine

A tiny command-line comedian. You give it a topic, it writes a joke, and you
can keep pushing that joke in one of two directions — **dark & crude** or
**clean & clever** — until you like it.

```
$ python tell_me_a_joke.py
Enter a joke topic: hexagonal architecture

Why did the architect refuse to leave the house?
Every exit was behind a port he hadn't implemented yet.

[a] Accept  [d] Rewrite dark & crude  [c] Rewrite clean & clever  [q] Quit
Your choice:
```

## Why this project exists

This is a learning project. The joke engine is the excuse; the real goal is to
get hands-on with [LangGraph](https://langchain-ai.github.io/langgraph/) and
see what it actually buys you when you build an LLM workflow with it:

- **Explicit state.** The graph's state is a plain `TypedDict`.
- **A shape that can grow.** Adding a critic node or a retry edge means editing
  the graph, not untangling imperative code.
- **Conversation as input.** Each rewrite replays the revision chain, so the
  model escalates instead of repeating itself.

LangGraph stays behind one port implementation — the domain and use case know
nothing about it, so swapping it out is a one-file change.

## Setup

Requires Python 3.10+ and an [Anthropic API key](https://console.anthropic.com/).

1. Copy the environment template and add your key:

   ```bash
   cp .env-template .env
   ```

   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

```bash
python tell_me_a_joke.py
```

Enter a topic when prompted. After each joke you can:

| Key | Action                                                     |
| --- | ---------------------------------------------------------- |
| `a` | Accept the joke and exit                                   |
| `d` | Rewrite it darker and cruder                               |
| `c` | Rewrite it cleaner and more clever                         |
| `q` | Quit                                                       |

Rewrites stack. Pressing `d` twice doesn't give you the same joke twice — the
second request tells the model its previous attempt didn't go far enough and
asks it to push past every version so far.

## Configuration

All configuration is environment variables, read from `.env` or the shell
(an already-set shell variable always wins over `.env`).

| Variable            | Default            | Purpose                                            |
| ------------------- | ------------------ | -------------------------------------------------- |
| `ANTHROPIC_API_KEY` | —                  | Required.                                          |
| `JOKE_ENGINE_MODEL` | `claude-haiku-4-5` | Any Claude model id.                               |
| `JOKE_ENGINE_EFFORT`| `low`              | Reasoning effort, for models that support it.      |

The defaults are the cheapest combination that still tells a decent joke.

## Architecture

Hexagonal (ports & adapters), so the interesting parts stay testable without
touching the network:

```
       CLI (inbound adapter)
                │
        TellJokeUseCase          application
                │
        JokeGenerator            port (Protocol)
                │
    LangGraphJokeGenerator       outbound adapter
                │
      LangGraph → ChatAnthropic → Claude
```

```
joke_engine/
├── domain/            Joke, Revision, JokeGeneration, RewriteStyle — validation only
├── ports/             JokeGenerator protocol + JokeGenerationError
├── application/       TellJokeUseCase
└── adapters/
    ├── inbound/       cli.py — prompts, review loop, error messages
    └── outbound/      langgraph_joke_generator.py + prompt resources
```

A few things worth knowing:

- **The domain is pure data.** `JokeGeneration` enforces its own invariants
  (non-empty topic and text, the first revision has no style, every later one
  does), so an unusable model reply can't sneak into the chain.
- **Every failure crosses the port as `JokeGenerationError`.** API errors,
  network errors, missing credentials and empty replies are all translated in
  the adapter, so the CLI has exactly one exception type to handle — and a
  failed rewrite keeps the joke you already have instead of ending the session.
- **Prompts are files, not string literals.** They live in
  `adapters/outbound/resources/`, one per persona.

## Tests

```bash
pytest
```

The suite mirrors the package layout. The use-case and CLI tests stub the
`JokeGenerator` port; the adapter tests fake the chat model. Nothing hits the
Anthropic API, so `pytest` needs no key.

## Project workflow

Changes are specced with [OpenSpec](https://github.com/Fission-AI/OpenSpec)
under `openspec/` before they're implemented. `AGENTS.md` holds the commit
conventions.
