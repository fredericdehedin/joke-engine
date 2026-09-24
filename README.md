# Joke Engine

## Setup

1. Copy `.env-template` to `.env`:

   ```bash
   cp .env-template .env
   ```

2. Open `.env` and add your Anthropic API key:

   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Starting the engine

```bash
python tell_me_a_joke.py
```

You'll be prompted to enter a joke topic, and the engine will print a joke back.
