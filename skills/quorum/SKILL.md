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

1. **Let the user pick providers and models.** Call `quorum_list_models` first. Only providers
   with status `ok` are offered. Ask with your host's question tool if it has one
   (`AskUserQuestion` in Claude Code: at most 4 questions per call, 2–4 options each, plus a
   free-text "Other"), otherwise in chat, and wait for each answer:
   - **Round 1, level and providers.** Level, single choice: `quick` (fast models, low effort),
     `balanced` (workhorse, medium) or `deep` (flagship, high; slowest, heaviest on quota). It
     only sets the preselected model and effort per provider (`preselected` in the catalog).
     Providers, multi-select, at least two participants in total. Agents first; mark API and
     local ones as "no project or web access". When more than four providers are available,
     list them in chat and let the user answer with names.
   - **Round 2, one model per chosen provider** (up to four questions per call; more providers,
     more calls). The first option is the preselected model, marked "(Recommended)", followed
     by up to two other models from that provider's catalog entry. The user can type any other
     listed model or `model@effort` under "Other". Skip providers with a single model.

   Skip what the user's request already answers ("a deep Quorum with claude and gpt-5.5").
   Build ids `provider:model@effort` from the catalog, leaving effort off for providers whose
   `efforts` list is empty, and put the strongest first because the first participant writes the
   synthesis. Pass them as `participants`.
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
