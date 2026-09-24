---
name: quorum
description: Run a structured debate between agent CLIs (claude, codex, agy) through the Quorum MCP tools. Use only when the user explicitly asks for a Quorum, a debate, a multi-agent discussion, or a second opinion from other models — never on your own initiative.
---

# Quorum

Quorum puts one question to several agent CLIs. They research read-only in the project and
on the web, debate in structured phases, and the first participant writes a synthesis. Runs
take minutes and spend the user's subscription quota, which is why a run only starts when the
user asks for one.

## Flow

1. **Pick participants.** Map the user's wording to a preset when it fits: "quick" → `quick`,
   no qualifier → `balanced`, "deep"/"thorough"/high stakes → `deep`. Presets give one
   participant per available agent, so three model families argue. When the user names models,
   agents or effort, call `quorum_list_models` and build explicit ids
   `agent:model@effort` from its catalog. Use only model ids that the catalog lists, because
   they are current. Put the strongest participant first, since it writes the synthesis.
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

- `quorum_start` names the unavailable agent or unknown model. Fix the ids, or tell the user
  which login is missing (`claude auth login`, `codex login`, or `agy` interactively).
- A dropped participant does not stop the run. It fails only if fewer than two remain.
- `quorum_check` does a real ping to every agent. Use it when the user asks whether Quorum
  works, or after an unexplained failure.
