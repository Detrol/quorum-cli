# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- Changes after 1.0.7 release go here -->

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

[Unreleased]: https://github.com/Detrol/quorum-cli/compare/v1.0.7...HEAD
[1.0.7]: https://github.com/Detrol/quorum-cli/compare/v1.0.5...v1.0.7
[1.0.5]: https://github.com/Detrol/quorum-cli/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/Detrol/quorum-cli/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/Detrol/quorum-cli/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/Detrol/quorum-cli/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/Detrol/quorum-cli/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Detrol/quorum-cli/releases/tag/v1.0.0
