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

1. **Let the user pick providers, method, models and effort.** Call `quorum_list_models` first;
   offer only providers with status `ok`. Ask with your host's question tool if it has one
   (`AskUserQuestion` in Claude Code: at most 4 questions per call and 2–4 options per question),
   otherwise in chat, and wait for each answer.

   **Every choice must be reachable through the options themselves.** Do not count on a free-text
   "Other" answer; not every host offers one. When a choice has more than four values, show three
   and a fourth option "More…" that leads to a follow-up question with the next ones, repeating
   until all are shown.

   - **Round 1, providers and method** (one call).
     - *Agents*, multi-select: the agent providers (claude, codex, agy, grok) with status `ok`.
     - *API and local providers*, multi-select, marked "no project or web access": those with
       status `ok`, four per question (add another question for more). Leave the question out
       when none are available.
     - *Method*, single choice: the three methods (from `methods`) that fit the question best,
       the best one first and marked "(Recommended)", each with its `best_for`, plus
       "Other methods…", which leads to a follow-up question with the remaining four. Mind the
       counts: `oxford` needs an even number of participants, `advocate` and `delphi` three or
       more.
     At least two participants in total; if the user picked fewer, ask again.
   - **Round 2, model and effort per chosen provider** (two questions per provider, so two
     providers per call; more providers, more calls).
     - *Model*: that provider's models, the `workhorse` model (or else the first) first and
       marked "(Recommended)", then "More models…" when it has more than four. Each option's
       description gives the model's description and its effort levels (`efforts`), e.g.
       "Balanced model · effort: low–max". Skip the question for a provider with one model.
     - *Effort*, only when the provider has effort levels: "Default (Recommended)" (the
       provider's own default; send no `@effort`), `medium`, `high`, and "More levels…", which
       leads to a follow-up with the chosen model's remaining levels (`low`, `xhigh`, `max`, …).
       A level the chosen model lacks is clamped to the nearest one it has.

   In chat without a question tool, list each provider's models with their effort levels in one
   message and let the user answer in one line (e.g. "claude opus@high, codex gpt-6-sol,
   tradeoff"). Skip whatever the request already answers ("a Quorum with claude and gpt-5.5").
   Build ids `provider:model@effort`, leaving effort off for "Default", and put the strongest
   first, because with the default settings the first participant writes the synthesis.
2. **Give the question full context.** Participants see only the question, the files, and what
   agent participants look up themselves.
3. **Start** with `quorum_start`: `participants`, `method`, `cwd` = the absolute project root so
   agent participants read the right code, the full context in `question`, and `files` for
   specific files.
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
