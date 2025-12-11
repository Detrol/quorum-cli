# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

<!-- Changes after 1.0.0 release go here -->

---

## [1.0.0] - 2025-12-10

Initial release of Quorum - a multi-agent AI discussion system built on AutoGen.

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
- `QUORUM_EXPORT_FORMAT` - Default export format (md/text/pdf)

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

[Unreleased]: https://github.com/Detrol/quorum-cli/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Detrol/quorum-cli/releases/tag/v1.0.0
