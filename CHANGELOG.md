# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-09-25

### Added

- **API and local providers in MCP again** - the models in `~/.quorum/.env` (OpenAI, Anthropic, Google, xAI, OpenRouter, LM Studio, llama-swap, custom, Ollama) take part alongside agent CLIs, as `provider:model@effort`
- Effort for API models: `reasoning_effort` (OpenAI, Google, xAI) and adaptive thinking with `output_config.effort` (Anthropic); only sent when chosen
- `quorum_list_models` lists every provider with kind, tools and status
- `quorum_discuss` is back as a deprecated, blocking v1.1-compatible tool; bare `*_MODELS` ids work in all tools
- `QUORUM_METHOD` sets the default method in MCP (documented before, but never read)

### Changed

- **Lineup form**: `quorum_start` without participants shows the user a form (MCP elicitation) with one dropdown per available provider (off, or model with effort) and the method, preset to the last lineup (`~/.quorum/last_lineup.json`). Clients without form support fall back to chat. The Codex plugin raises the MCP tool timeout to 900 s so the open form is not cut off
- MCP respects `QUORUM_SYNTHESIZER` instead of always using the first participant
- MCP always reads `~/.quorum/.env`, never a `.env` in the calling agent's project directory
- **Presets removed** (`quick`/`balanced`/`deep`, and `preset`/`agents` on `quorum_start`): participants are always the models the user picked. Effort is sent only when given as `@effort`

### Fixed

- v1.2.0 removed API and Ollama models from the MCP server that v1.1.x documented; restored

## [1.4.0] - 2026-09-25

### Added

- `quorum_start` takes `agents` to limit a preset to the agents the user picked

### Changed

- The `quorum` skill and the `quorum_start` description now have the calling agent ask the user for level (`quick`/`balanced`/`deep`) and agents before starting, unless the request already says
- agy effort now picks the model variant (`gemini-3.1-pro@high` → `gemini-3.1-pro-high`); agy has no effort flag. The catalog lists agy models by base with their variants as efforts
- Presets fall back to an agent's workhorse model before its first model

### Fixed

- A CLI that saves a refreshed token by rename (grok) broke the user's own login: the rotated token stayed in the isolation home. Refreshed tokens are now copied back to the real login after every agent process, and the link restored

## [1.3.0] - 2026-09-25

### Added

- **grok as agent participant** - `grok:<model>@effort` via the grok CLI on the user's own subscription
  - Read-only tools (`read_file`, `list_dir`, `grep`, `web_fetch`) with web fetch allowed on every domain
  - Isolated home plus harness-compat switches off, so no rules, skills, plugins, hooks or MCP servers are loaded
  - Efforts `low`–`xhigh`; `max` clamps to `xhigh`

### Changed

- Presets fall back to an agent's first model when it has no role tiers (grok lists one default model)

### Fixed

- Isolation homes relink the user's login when a CLI replaced the symlink with a refreshed copy

## [1.2.0] - 2026-09-24

### Added

- **Agent participants** - claude, codex and agy (Antigravity) take part in discussions via their CLIs, on the user's own subscription
  - Read-only project access plus web search; isolated from the user's hooks, plugins, MCP servers and instruction files
  - Participant ids `agent:model@effort`, with one effort scale clamped to what each model supports
  - Model catalog discovered from each CLI (cached for 1 h) and presets by role: `quick`, `balanced`, `deep`
- **Claude Code & Codex plugin** - `.claude-plugin/`, `.codex-plugin/`, a shared `quorum` skill and `.mcp.json`
- **MCP tools** `quorum_start` / `quorum_wait` (runs survive client tool timeouts) and `quorum_check` (real ping)

### Changed

- MCP server exposes only agent participants; `quorum_discuss` is replaced by `quorum_start` + `quorum_wait`
- MCP errors are returned as real tool errors instead of a fake synthesis
- A dropped participant is skipped for the rest of the run, including as synthesizer

### Fixed

- MCP server crashed on start with `mcp` 2.x; dependency pinned to `mcp<2`
- MCP server reported a hard-coded version

## [1.1.5] - 2025-12-25

### Added

- **Language Selector** - Choose response language directly in the UI
  - New dropdown in header: English, Swedish, German, French, Spanish, Italian
  - Setting persisted across sessions
  - MCP mode defaults to "match question language" for backwards compatibility

- **EVOLUTION Section in Synthesis** - Shows how positions developed during discussion
  - Summarizes convergence patterns and position changes
  - Based only on what models explicitly stated (prevents fabrication)
  - Makes Quorum's value visible to users who skip to the synthesis

### Changed

- **Phase 4 Honest Reflection** - Reduced sycophancy in final positions
  - Prompt now asks models to explain WHY position evolved OR why they maintained it
  - "Both outcomes are valid - honest reflection matters more than forced evolution"
  - Prevents fabricated "learning" claims when original position was already correct

- **Key Insight Quality** - Removed unverifiable counterfactual claims
  - Changed from "Something they'll remember and quote"
  - To "The most robust or actionable perspective"
  - Added: "Do NOT claim what a single AI would miss - you cannot observe that"

- **Genuine Debates** - Anti-sycophancy improvements across all methods
  - Critique: Stronger language normalizing disagreement
  - Oxford: EVOLUTION section in judgement showing how arguments developed
  - Advocate: Explicit value of honest concession over weak defense
  - Socratic: THESIS_EVOLUTION tracking concrete position changes
  - Tradeoff: EVALUATOR_ALIGNMENT showing recommendation consensus

---

## [1.1.4] - 2025-12-22

### Changed

- **Local-first config loading** - When `./.env` exists in current directory, use it exclusively
  - Previously loaded both `~/.quorum/.env` and `./.env` and merged them
  - Now uses local-first priority: local `.env` if present, otherwise global `~/.quorum/.env`
  - Prevents confusing merged model lists when running from different project directories

- **Improved Synthesis Format** - More actionable and structured output
  - New sections: Bottom Line, Key Insight, The Answer, Important Caveats
  - Quality requirements ensure direct, memorable, and specific answers
  - For communication questions, includes sample scripts to adapt

### Fixed

- **Phase 4 Insight Preservation** - Final positions now include full discussion context
  - Previously, Phase 3 discussion was not passed to Phase 4, causing models to lose valuable insights
  - Now `_discussion_messages` stores the complete Phase 3 discussion and passes it to `get_final_position_prompt()`
  - Prompt updated to encourage including "specific thresholds, frameworks, or conditions" from discussion
  - Removed "be concise" instruction that triggered information loss

- **Socratic Method Prompt** - Changed "Be concise but complete" to "Be thorough and complete"
  - Prevents respondents from over-compressing their answers

- **Selected models filtering** - Cached selected models are now filtered against available models
  - Previously, switching configs could show stale models from old config
  - Now `selected_models` in `~/.quorum/settings.json` is filtered to only show available models

---

## [1.1.3] - 2025-12-21

### Changed

- **MCP Tool Descriptions** - Improved guidance for Claude Code/Desktop integration
  - `quorum_list_models`: Now instructs to "ALWAYS call this before quorum_discuss"
  - `quorum_discuss`: Explicitly mentions checking models first and file context use cases
  - `files` parameter: Better explains when to use (code review, document comparison, analysis)
  - `full_output`: Clarifies "only use if user explicitly asks"

- **WSL + Windows Ollama** - Improved README with complete 3-step setup guide

---

## [1.1.2] - 2025-12-15

### Added

- **MCP File Context** - Pass files directly to discussions via `files` parameter
  - MCP server reads files and includes them as context
  - Limits: max 10 files, 100KB per file, 500KB total
  - Reports `files_included` count and `file_errors` in response

### Changed

- **Auto GitHub Releases** - Tags now automatically create GitHub Releases
  - Extracts changelog notes for the tagged version
  - Attaches `.whl` artifact to release

---

## [1.1.1] - 2025-12-14

### Fixed

- **MCP Error Handling** - Added try/except for runtime errors during discussions
  - API failures, timeouts, and unexpected errors now return structured JSON responses
  - Improved tool description with model requirements (min 2, Oxford=even, Advocate/Delphi=3+)

- **Test Compatibility** - Fixed `_write_json` to handle StringIO in tests
  - Falls back to regular write when `stdout.buffer` not available
  - Resolves 8 failing tests in CI

- **Pytest Collection** - Excluded MCP module from test collection
  - MCP requires `mcp` dependency not installed in test environment
  - Added `src/conftest.py` with `collect_ignore`

---

## [1.1.0] - 2025-12-14

### Added

- **MCP Server** - Model Context Protocol integration for Claude Code/Desktop
  - New `quorum-mcp-server` command for MCP integration
  - Install once, use everywhere: `claude mcp add quorum -- quorum-mcp-server`
  - **Tools:**
    - `quorum_discuss` - Run multi-model discussions with any method
    - `quorum_list_models` - List configured models
  - **Resources:**
    - `quorum://models` - Available models per provider
    - `quorum://methods` - The 7 discussion methods with descriptions
  - Compact output by default (synthesis only) - saves ~90% context
  - Set `full_output: true` for complete discussion transcript
  - Reuses existing `~/.quorum/.env` config - no duplicate API keys needed

- **Message Render Delay** - Added 150ms delay between content messages
  - Gives frontend time to process and render messages
  - Only applies to content events (answers, critiques, positions)
  - Control messages (phase markers, thinking indicators) are not delayed

### Fixed

- **Windows Unicode Output** - Fixed IPC stdout encoding for Windows
  - Model responses containing Unicode characters (≥, ≤, →, etc.) now display correctly
  - Changed JSON output to write UTF-8 bytes directly to `stdout.buffer`
  - Windows default stdout uses cp1252 which can't encode all Unicode characters
  - Primarily affected GPT models which often include math symbols in responses

---

## [1.0.7] - 2025-12-13

### Added

- **PyPI Distribution** - Install Quorum with a single command
  - `pip install quorum-cli && quorum` now works out of the box
  - Frontend is bundled into the wheel automatically
  - GitHub Actions workflow for automated PyPI publishing with Trusted Publishing
- **First-run Setup** - Automatic configuration setup for pip users
  - Creates `~/.quorum/.env.example` on first run
  - Shows friendly setup instructions
  - Config loaded from `~/.quorum/.env` (no need to be in specific directory)

### Fixed

- **Startup Spinner** - Animated loading spinner now shows immediately on all platforms
  - Works consistently for both pip install and development mode
  - Signal file coordination between launcher and frontend
- **Modal ESC Handling** - `/help` and `/status` modals can now be closed with ESC key

### Changed

- Simplified launcher scripts (removed signal file complexity from user-facing code)
- Frontend now signals readiness to launcher for seamless spinner-to-UI transition

---

## [1.0.5] - 2025-12-13

### Fixed

- **Windows Native Support** - Fixed critical issues preventing Windows .bat launcher from working
  - Fixed `PROJECT_ROOT` detection in frontend using `import.meta.url` instead of `process.cwd()`
  - Fixed Python asyncio stdin reading using `run_in_executor` (cross-platform)
  - Python's `connect_read_pipe` doesn't work on Windows (ProactorEventLoop: WinError 6, SelectorEventLoop: NotImplementedError)
  - Quorum now works correctly when launched from `quorum.bat` on Windows

---

## [1.0.4] - 2025-12-12

### Changed

- **Ollama Model Discovery** - Non-generative models are now automatically filtered
  - Embedding models (`nomic-embed-text`, `bge-m3`, etc.) are hidden from `/models`
  - Whisper/speech-to-text models are also filtered
  - Vision models (llava, gemma3, etc.) are NOT filtered - they can generate text
  - Prevents users from selecting models that would fail with "does not support generate"

---

## [1.0.3] - 2025-12-12

### Added

- **Adaptive Execution Mode** - Smart VRAM management for local Ollama models
  - New `QUORUM_EXECUTION_MODE` setting: `auto`, `parallel`, `sequential`
  - `auto` (default): Cloud APIs run in parallel, Ollama runs sequentially
  - Prevents VRAM competition when running multiple local models
  - No configuration needed - works automatically for Ollama users

- **OpenAI-Compatible Providers** - Connect to any OpenAI-format API
  - **OpenRouter**: Access 200+ models through one API key
  - **LM Studio**: Local models with GUI (no API key required)
  - **llama-swap**: Hot-swap server for local models
  - **Custom**: Generic fallback for any OpenAI-compatible endpoint
  - Use multiple providers simultaneously (e.g., OpenRouter + llama-swap)
  - Models appear in `/models` alongside native providers

---

## [1.0.2] - 2025-12-12

### Changed

- **Removed AutoGen dependency** - Replaced with direct SDK clients
  - New `clients/` module with `OpenAIClient` and `AnthropicClient`
  - ~50MB smaller install footprint
  - Faster startup time
  - No functional changes for users

### Internal

- Added `ChatClient` protocol for unified client interface
- Created ADR-0003 documenting the AutoGen removal decision
- Superseded ADR-0002 (AutoGen for orchestration)

---

## [1.0.1] - 2025-12-12

### Added

- **JSON Export** - Structured JSON export with method-specific schemas (`/export json`)
  - Each discussion method has its own schema (Standard, Oxford, Advocate, Socratic, Delphi, Brainstorm, Tradeoff)
  - Synthesis/verdict/decision included in final phase messages
  - Schema version 2.0 with full metadata

### Changed

- **Unified Export Architecture** - PDF and JSON now use the same method-aware parser
  - Consistent phase structure across all export formats
  - Removed legacy generic parser

---

## [1.0.0] - 2025-12-10

Initial release of Quorum - a multi-agent AI discussion system for structured debates.

### Discussion Methods

Seven distinct methods for orchestrating AI discussions:

- **Standard** - Balanced 5-phase consensus seeking (2+ models)
  - Independent answers → Structured critique → Round-robin discussion → Final positions → Synthesis
- **Oxford** - Formal debate with FOR/AGAINST teams (even number of models)
  - Opening statements → Rebuttals → Closing statements → Verdict
- **Advocate** - Devil's advocate mode (3+ models)
  - Last model challenges emerging consensus while others defend
- **Socratic** - Guided questioning dialogue (2+ models)
  - Rotating questioner deepens understanding through inquiry
- **Delphi** - Iterative expert estimation (3+ models)
  - Anonymous estimates → Revision rounds → Convergence analysis
- **Brainstorm** - Creative ideation (2+ models)
  - Diverge → Build on ideas → Converge → Selection
- **Tradeoff** - Multi-criteria decision analysis (2+ models)
  - Frame alternatives → Define criteria → Evaluate → Recommend

### AI Provider Support

- **OpenAI** - GPT-5, GPT-5.1, GPT-5.2 models
- **Anthropic** - Claude Sonnet 4.5, Claude Opus 4.5 models
- **Google** - Gemini 3 Pro, Gemini 2.5 Flash models
- **xAI** - Grok 4, Grok 4.1 models
- **Ollama** - Local models with auto-discovery
  - Models appear automatically when pulled (`ollama pull llama3`)
  - Extended timeouts (60s) for GPU loading
  - Support for remote Ollama servers

### Terminal User Interface

- React/Ink-based terminal UI with rich formatting
- Model selection with multi-provider support (`/models`)
- Method selection with inline shortcuts (`/oxford`, `/socratic`, etc.)
- **Method Advisor** - AI-powered method recommendations (Tab or `/advisor`)
- Phase-by-phase progress with pause between phases
- Thinking indicators showing which model is responding
- Input history with arrow key navigation
- Export discussions to Markdown, Text, or PDF (`/export`)
- **Internationalization** - UI in 6 languages (English, Swedish, German, French, Spanish, Italian)

### Backend Architecture

- **JSON-RPC 2.0** IPC protocol with versioning (v1.0.0)
- **Connection Pooling** - LRU-based pool (20 clients max) for connection reuse
- **Rate Limiting** - Token bucket algorithm (60 req/min, burst 10)
- **Discussion Sessions** - Unique IDs for event filtering and cancellation
- **Pause/Resume** - User-controlled phase transitions
- **Graceful Cancellation** - ESC/Ctrl+R cleanly terminates discussions

### Security & Validation

- Model ID sanitization with character validation
- Question length limits (50KB max)
- Request size limits (1MB max JSON)
- Prompt injection protection in Method Advisor
- No secrets in logs or exports

### Configuration

Environment variables (`.env`):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`
- `*_MODELS` - Comma-separated model lists per provider
- `QUORUM_ROUNDS_PER_AGENT` - Discussion rounds (1-10)
- `QUORUM_SYNTHESIZER` - Synthesizer mode (first/random/rotate)
- `QUORUM_DEFAULT_LANGUAGE` - Force response language
- `QUORUM_EXPORT_FORMAT` - Default export format (md/text/pdf/json)

User cache (`~/.quorum/`):
- `validated_models.json` - Cached model availability
- `settings.json` - UI preferences
- `history.json` - Question history

### Installation

- Cross-platform support (Linux, macOS, Windows, WSL)
- Simple install scripts (`install.sh`, `install.bat`)
- `uv` package manager for fast dependency resolution
- Node.js frontend build with npm

### Developer Features

- Comprehensive test suite (300+ tests)
- Protocol versioning for frontend-backend compatibility
- Lazy-loading method orchestrators for fast startup
- Structured message types for all discussion events
- Auto-save discussions to `reports/` directory

---

[1.1.5]: https://github.com/Detrol/quorum-cli/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/Detrol/quorum-cli/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/Detrol/quorum-cli/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/Detrol/quorum-cli/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/Detrol/quorum-cli/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/Detrol/quorum-cli/compare/v1.0.7...v1.1.0
[1.0.7]: https://github.com/Detrol/quorum-cli/compare/v1.0.5...v1.0.7
[1.0.5]: https://github.com/Detrol/quorum-cli/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/Detrol/quorum-cli/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/Detrol/quorum-cli/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/Detrol/quorum-cli/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Detrol/quorum-cli/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Detrol/quorum-cli/releases/tag/v1.0.0
