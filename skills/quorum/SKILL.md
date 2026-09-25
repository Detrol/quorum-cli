---
name: quorum
description: Run a structured debate between agent CLIs (claude, codex, agy, grok) and the user's configured API or local models (OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama and more) through the Quorum MCP tools. Use only when the user explicitly asks for a Quorum, a debate, a multi-agent discussion, or a second opinion from other models — never on your own initiative.
---

# Quorum

Quorum puts one question to several models. Agent CLIs (claude, codex, agy, grok) research
read-only in the project and on the web; API and local models configured in `~/.quorum/.env`
(openai, anthropic, google, xai, openrouter, lmstudio, llamaswap, custom, ollama) see only the
question and any files passed. They debate in structured phases and one participant writes the
synthesis. Runs
take minutes and spend the user's subscription quota, which is why a run only starts when the
user asks for one.

## Flow

1. **Let the user pick providers, then models.** Call `quorum_list_models` first; offer only
   providers with status `ok`. Ask with your host's question tool if it has one
   (`AskUserQuestion` in Claude Code: at most 4 questions per call, 2–4 options each, plus a
   free-text "Other"), otherwise in chat, and wait for each answer.
   - **Round 1, providers**, multi-select, at least two participants in total. Agents first; mark
     API and local providers "no project or web access". When more than four providers are
     available, list them in chat and let the user answer with names.
   - **Round 2, one model per chosen provider** (up to four questions per call; more providers,
     more calls), options taken from that provider's catalog entry with their descriptions. Mark
     the provider's `workhorse` model, or else its first model, "(Recommended)". The user can type
     any other listed model, or `model@effort`, under "Other". Skip the question for a provider
     with a single model.

   Skip whatever the request already answers ("a Quorum with claude and gpt-5.5"). Add `@effort`
   only when the user asks for one; otherwise each provider uses its own default. Build ids
   `provider:model@effort` and put the strongest first, because with the default settings the
   first participant writes the synthesis. Pass them as `participants`.
2. **Pick a method** when the question calls for one (see `methods` in `quorum_list_models`):
   `tradeoff` for A-vs-B, `delphi` for estimates, `advocate` to stress-test a plan, `oxford`
   for a for/against debate (even count), `brainstorm` for ideas. Otherwise `standard`.
3. **Start** with `quorum_start`. Pass `cwd` = the absolute project root so participants read
   the right code. Put the full context they need in `question`, because participants see only
   the question, the files, and what they look up themselves. Add `files` for specific files.
4. **Wait** with `quorum_wait` in a loop until `status` is `done` or `failed`. Tell the user the
   phase once in a while; do not print every poll.
5. **Report.** Give the consensus level, the synthesis, the real disagreements, and anything
   dropped. Add your own view only when it differs, and label it as yours. Fetch the full
   transcript (`full: true`) only when the user asks for it.

## When something fails

- `quorum_start` names the unavailable provider or unknown model. Fix the ids, or tell the user
  what is missing: an agent login (`claude auth login`, `codex login`, `grok login`, or `agy`
  interactively), or an API key / `*_MODELS` entry in `~/.quorum/.env`.
- A dropped participant does not stop the run. It fails only if fewer than two remain.
- `quorum_check` does a real ping to every agent. Use it when the user asks whether Quorum
  works, or after an unexplained failure.
