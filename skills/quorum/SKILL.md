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

1. **Write the question with full context.** Participants see only the question, the files you
   pass, and what agent participants look up themselves in the project and on the web.
2. **Start** with `quorum_start`: the question, `cwd` = the absolute project root, and `files`
   for specific files. Leave out `participants` and `method`: the server shows the user a form
   with one dropdown per available provider (off, or a model with an effort level) and the
   method, preset to their last lineup. Pass `participants` (`provider:model@effort`, strongest
   first) and `method` only when the user already named them.
   - Status `cancelled`: the user closed the form. Say so and stop.
   - Error "cannot show a form": this client has no form support. Call `quorum_list_models`,
     list each available provider's models with their effort levels and the methods in one chat
     message, ask the user to answer in one line (e.g. "claude opus@high, codex gpt-6-sol,
     tradeoff"), then call `quorum_start` again with `participants` and `method`.
3. **Wait** with `quorum_wait` in a loop until `status` is `done` or `failed`. Tell the user the
   phase once in a while; do not print every poll.
4. **Report.** Give the consensus level, the synthesis, the real disagreements, and anything
   dropped. Add your own view only when it differs, and label it as yours. Fetch the full
   transcript (`full: true`) only when the user asks for it.

## When something fails

- `quorum_start` names the unavailable provider or unknown model. Fix the ids, or tell the user
  what is missing: an agent login (`claude auth login`, `codex login`, `grok login`, or `agy`
  interactively), or an API key / `*_MODELS` entry in `~/.quorum/.env`.
- A dropped participant does not stop the run. It fails only if fewer than two remain.
- `quorum_check` does a real ping to every agent. Use it when the user asks whether Quorum
  works, or after an unexplained failure.
