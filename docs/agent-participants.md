# Spec: Agent Participants + MCP plugin

Goal: let Claude Code and Codex (on the user's request, never automatically) run a Quorum
Discussion between agent CLIs — claude, codex, agy, grok — with deliberate model and Effort choice.
Terms: see `CONTEXT.md`.

## Decisions

| # | Decision |
|---|----------|
| Participants | Agent CLIs only on the MCP surface. API clients stay for the TUI. |
| Access | Read-only in the project + web search. No writes. |
| Isolation | Participants never load the user's hooks, plugins, skills, MCP servers, memory or instruction files (global or project). Nested Runs refused (`QUORUM_PARTICIPANT=1`). |
| Model choice | Catalog discovered from each CLI (1 h cache); Presets resolve by role; the caller may pass exact Participants. |
| Effort | Per Participant on one scale, default per Run. |
| Liveness | Discovery checks binary + login (free). Phase 1 is the ping. `quorum_check` does a real ping on request. |
| Flow | `quorum_start` → `quorum_wait` in slices (safe under client tool timeouts). |
| Failure | Dropped Participants are reported; the Run aborts when fewer than 2 remain. |
| Synthesis | First Participant writes it. Result: consensus, synthesis, differences, per-Participant final position (standard method), dropped list. Full transcript on request. |
| Limits | ≤4 Participants, 10 min per turn, 30 min per Run, one active Run per project directory. Overridable per call. |
| Packaging | One repo, `.claude-plugin/` + `.codex-plugin/` sharing `skills/` and `.mcp.json`; server launched via `uvx --from quorum-cli quorum-mcp-server`. |

## Verified CLI invocations (2026-09-24)

- **claude 2.1**: `claude -p --model <alias|id> --effort <e> --setting-sources "" --strict-mcp-config
  --disable-slash-commands --no-session-persistence --tools Read,Grep,Glob,WebSearch,WebFetch
  --allowedTools <same> --output-format json`, env `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`,
  `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. `--bare` is unusable: it refuses OAuth (subscription) auth.
  Aliases: fable, opus, sonnet, haiku. Login: `claude auth status`.
- **codex 0.156**: `codex --search exec -m <slug> -c model_reasoning_effort=<e> -c project_doc_max_bytes=0
  -s read-only --skip-git-repo-check --ephemeral -o <file> -` with an isolated `CODEX_HOME` holding only a
  symlink to `auth.json` (drops config, hooks, plugins, global AGENTS.md). `--search` is a top-level flag.
  Catalog: `codex debug models` (`visibility == "list"`, `priority` 1 = frontier, 2 = workhorse, 3 = fast).
- **agy 1.2**: `agy --model <base>-<low|medium|high> --sandbox --add-dir <cwd> --output-format json
  --print=<prompt>` with an isolated `HOME` holding symlinks to the OAuth files and a generated
  `settings.json` whose `permissions.allow` lists read/web tools and `permissions.deny` lists
  command/write/edit. Headless mode auto-denies unlisted tools and then aborts the whole answer; an explicit
  deny lets the model continue. `--mode plan` is prompt-only and is ignored with
  `--disable-slash-commands`, so it is not used. `--effort` has no effect with gemini models: effort is the
  model variant suffix, so the catalog groups variants by base. Catalog: `agy models` (also proves login).

- **grok 1.0** (added 2026-09-25): `grok --prompt-file <file> --model <id> --effort <low..xhigh>
  --tools read_file,list_dir,grep,web_fetch --allow read_file --allow list_dir --allow grep --allow WebFetch
  --no-subagents --output-format json` with `HOME` set to an isolated dir holding only a symlink to
  `~/.grok/auth.json`, plus `GROK_{CLAUDE,CODEX,CURSOR}_{AGENTS,HOOKS,MCPS,RULES,SKILLS,SESSIONS}_ENABLED=0`
  (grok otherwise imports Claude/Codex/Cursor rules, skills, plugins, hooks and MCP servers). Headless mode
  cancels the whole turn on any permission prompt; `web_fetch` prompts outside a built-in domain allowlist,
  hence `--allow WebFetch`. There is no web search tool, only fetch. Catalog: `grok models` (`* id (default)`),
  which also proves login; the first call after idle can race a token refresh, so discovery retries once.
  Project-level `.grok/config.toml`, `.mcp.json`, `.grok/rules`, project skills and `AGENTS.md` stay unloaded
  because the isolated home has no trusted folders, so every project is untrusted (verified 2026-09-25 with
  marker MCP servers that were never started). Do not add trusted folders to the isolated home.

- **Login files**: isolation homes symlink each CLI's login. grok saves a refreshed, rotated token by
  renaming a new file into place, which replaced the symlink and left the user's own login invalid
  (seen 2026-09-25). After every agent process a newer regular file is copied back over the real login
  and relinked (`_resync_logins`). `GROK_AUTH_PATH` and `GROK_AUTH_PROVIDER_ACCESS_TOKEN` did not work.

## Tasks

1. `src/quorum/clients/agent_cli.py`: Participant parsing, Effort clamping, per-Agent command building,
   isolation homes, async subprocess with kill on cancel, catalog discovery + cache, Presets, ping.
2. Route `agent:` model ids in `models.py`; per-turn timeout via a contextvar in `methods/base.py`
   (also phase timeout and standard phase 1).
3. Rewrite `mcp/__init__.py`: tools `quorum_list_models`, `quorum_start`, `quorum_wait`, `quorum_check`;
   in-process Run registry; transcript to `~/.quorum/runs/<id>.json`; real MCP errors; version from
   `__version__`.
4. Plugin files: `.claude-plugin/{plugin,marketplace}.json`, `.codex-plugin/plugin.json`,
   `.agents/plugins/marketplace.json`, `.mcp.json`, `skills/quorum/SKILL.md`.
5. Tests: `tests/test_agent_cli.py` (pure logic + a fake CLI subprocess). Live smoke test of one real
   Run through the MCP server.
6. Pin `mcp<2`, bump to 1.2.0, CHANGELOG. No `v*` tag push without explicit approval.
