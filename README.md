# Quorum

<p align="center">
  <img src="docs/demo.gif" alt="Quorum - AI models debating in terminal" width="700">
</p>

<p align="center">
  <strong>AI War Room in your terminal.</strong><br>
  Watch GPT, Claude, Gemini, and Grok debate using formal methods.
</p>

<p align="center">
  <a href="https://github.com/Detrol/quorum-cli/actions/workflows/ci.yml"><img src="https://github.com/Detrol/quorum-cli/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-BSL_1.1-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
</p>

---

Multi-agent AI discussion system for structured debates. Ask multiple AI models (Claude, GPT, Gemini, Grok, and local models via Ollama) a question and let them debate, brainstorm, or deliberate using seven different methods.

## Quick Install (pip)

```bash
pip install quorum-cli
quorum
```

On first run, Quorum creates `~/.quorum/.env.example`. Copy and edit it:

```bash
cp ~/.quorum/.env.example ~/.quorum/.env
nano ~/.quorum/.env  # Add your API keys
quorum
```

**Upgrade:** `pip install -U quorum-cli`

**Requirements:** Python 3.11+, Node.js 18+

---

## Development Installation

For contributors or those who want the latest changes:

### Requirements

- Python 3.11 or higher
- Node.js 18 or higher
- npm
- [uv](https://github.com/astral-sh/uv) (auto-installed if missing)

### Linux / macOS

```bash
git clone https://github.com/Detrol/quorum-cli.git
cd quorum-cli
./install.sh
nano .env   # Add your API keys
./quorum
```

### Windows

```cmd
git clone https://github.com/Detrol/quorum-cli.git
cd quorum-cli
install.bat
notepad .env   & REM Add your API keys
quorum.bat
```

### Manual installation

```bash
# Install uv if not present
pip install uv

# Python dependencies (creates .venv automatically)
uv sync

# Frontend
cd frontend && npm install && npm run build && cd ..

# Configuration
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

## Configuration

Edit `.env` and add your API keys:

```bash
# OpenAI - https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...
OPENAI_MODELS=gpt-5.2,gpt-5.1,gpt-5

# Anthropic - https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODELS=claude-opus-4-5-20251124,claude-sonnet-4-5-20250929

# Google - https://aistudio.google.com/apikey
GOOGLE_API_KEY=...
GOOGLE_MODELS=gemini-3-pro,gemini-2.5-flash

# xAI (Grok) - https://console.x.ai/
XAI_API_KEY=xai-...
XAI_MODELS=grok-4.1,grok-4

# Ollama (local models) - https://ollama.com/
# Models are auto-discovered, no config needed for same-machine setup
# OLLAMA_BASE_URL=http://localhost:11434  # Default, change for remote
# OLLAMA_API_KEY=                          # Optional, for proxy authentication

# Optional settings
QUORUM_ROUNDS_PER_AGENT=2        # Discussion rounds per agent (1-10, default: 2)
QUORUM_SYNTHESIZER=first         # Who synthesizes: first, random, or rotate
QUORUM_DEFAULT_LANGUAGE=         # Force response language (e.g., "Swedish", "English")
# QUORUM_EXECUTION_MODE=auto     # VRAM optimization: auto, parallel, sequential
```

You only need to configure the providers you want to use. At least one provider is required.

### Finding available models

- **OpenAI**: https://platform.openai.com/docs/models
- **Anthropic**: https://docs.anthropic.com/en/docs/about-claude/models
- **Google**: https://ai.google.dev/gemini-api/docs/models
- **xAI (Grok)**: https://docs.x.ai/docs/models
- **Ollama**: https://ollama.com/library

### Ollama (Local Models)

Quorum supports local models via [Ollama](https://ollama.com/). Models are auto-discovered when Ollama is running.

**Quick start:**
```bash
# 1. Install Ollama from https://ollama.com/download
# 2. Pull a model
ollama pull llama3
# 3. Start Quorum - Ollama models appear automatically in /models
```

Models appear with `ollama:` prefix (e.g., `ollama:llama3`, `ollama:qwen3:8b`).

**VRAM management:** When using multiple Ollama models, Quorum automatically runs them sequentially to prevent VRAM competition. No configuration needed - it just works. See [Execution Mode](#execution-mode-vram-optimization) for advanced options.

### OpenAI-Compatible Providers

Quorum supports any service that uses the OpenAI API format. This lets you use OpenRouter, LM Studio, llama-swap, vLLM, LocalAI, and other compatible servers alongside native providers.

**OpenRouter** - Access 200+ models through one API:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODELS=anthropic/claude-3-opus,openai/gpt-4o,meta-llama/llama-3.1-70b
```

**LM Studio** - Local models with a GUI (no API key required):
```bash
LMSTUDIO_MODELS=llama-3.2-3b,deepseek-coder-v2
# LMSTUDIO_BASE_URL=http://localhost:1234/v1  # Default
```

**llama-swap** - Hot-swap between local models:
```bash
LLAMASWAP_BASE_URL=http://localhost:8080/v1
LLAMASWAP_MODELS=llama3,mistral-7b,qwen2
```

**Custom endpoint** - Any OpenAI-compatible server:
```bash
CUSTOM_BASE_URL=http://localhost:5000/v1
CUSTOM_MODELS=model-name-1,model-name-2
CUSTOM_API_KEY=your-key  # If required
```

Models from these providers appear in `/models` just like native providers. You can use them together with OpenAI, Anthropic, Google, xAI, and Ollama in the same discussion.

**Configuration scenarios:**

| Quorum runs on | Ollama runs on | Configuration |
|----------------|----------------|---------------|
| Windows | Windows | Works out of the box |
| Linux | Linux | Works out of the box |
| WSL | WSL | Works out of the box |
| WSL | Windows | See [WSL + Windows Ollama](#wsl--windows-ollama) below |
| Any | Remote server | Set `OLLAMA_BASE_URL` in `.env` |

**Remote Ollama server:**
```bash
# In .env
OLLAMA_BASE_URL=http://your-server:11434
OLLAMA_API_KEY=your-key  # Optional, if using authentication proxy
```

## Usage

### Start Quorum

```bash
quorum
```

### Select models

```
> /models

OPENAI
  [1] gpt-5.2
  [2] gpt-5.1

ANTHROPIC
  [3] claude-opus-4-5-20251124

GOOGLE
  [4] gemini-3-pro

Select models (comma-separated): 1,3,4
✓ Selected: gpt-5.2, claude-opus-4-5-20251124, gemini-3-pro
```

### Ask a question

```
> What is the best programming language for beginners?

╭─ gpt-5.2 ─────────────────────────────────────────╮
│ I would recommend Python for beginners...         │
╰───────────────────────────────────────────────────╯

╭─ claude-opus-4-5-20251124 ────────────────────────╮
│ I agree with the recommendation of Python...      │
│ CONSENSUS: Python is the best choice because...   │
╰───────────────────────────────────────────────────╯

╭─ gemini-3-pro ────────────────────────────────────╮
│ CONSENSUS: Python is recommended for beginners... │
╰───────────────────────────────────────────────────╯

──────────────────────────────────────────────────────

╭─ Result ──────────────────────────────────────────╮
│ CONSENSUS REACHED!                                │
│                                                   │
│ All 3 agents agreed.                              │
│ Messages exchanged: 3                             │
│                                                   │
│ Final Answer:                                     │
│ Python is recommended for beginners...            │
╰───────────────────────────────────────────────────╯
```

### Commands

| Command | Description |
|---------|-------------|
| `/models` | Select AI models for discussion |
| `/method [name]` | Show or set discussion method |
| `/advisor` or **Tab** | Get AI-powered method recommendation |
| `/synthesizer` | Set synthesizer mode (first/random/rotate) |
| `/status` | Show current settings |
| `/export [format]` | Export discussion (md, text, pdf, json) |
| `/clear` | Clear screen |
| `/help` | Show help |
| `/quit` or `/exit` | Exit Quorum |

## Discussion Methods

Quorum supports seven discussion methods that change how the discussion phase works. Each method has specific requirements for the number of models.

### Standard (default)

**Requires:** 2+ models

Balanced consensus-seeking discussion. All models discuss freely in a round-robin format, building on each other's ideas and critiques to find common ground.

**How it works:**
- Models take turns responding to the ongoing discussion
- Each model sees all previous answers and critiques
- Focus is on collaboration and synthesis

**Flow:**
```
Phase 1        Phase 2        Phase 3        Phase 4        Phase 5
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Answer  │ →  │Critique │ →  │ Discuss │ →  │Position │ →  │Synthesis│
│(parallel)│   │(parallel)│   │(turns)  │    │(parallel)│   │(single) │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
All models     Review each    Round-robin    Final stance   Synthesizer
respond        other's work   discussion     + confidence   aggregates
```

**Best for:** General questions, collaborative problem-solving, finding balanced answers.

```
> What's the best approach to error handling in this codebase?
```

---

### Oxford

**Requires:** Even number of models (2, 4, 6...)

Formal Oxford-style debate with assigned positions. Models are divided into FOR and AGAINST teams and must argue their assigned position regardless of personal opinion.

**How it works:**
1. **Opening statements** - Each side presents their strongest case
2. **Rebuttals** - Directly address and counter the opposing side's arguments
3. **Closing statements** - Summarize position and make final case

Models are assigned roles by index:
- Even indices (0, 2, 4...) argue **FOR**
- Odd indices (1, 3, 5...) argue **AGAINST**

**Flow:**
```
Phase 1         Phase 2         Phase 3         Phase 4
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│  Opening  │ → │ Rebuttals │ → │  Closing  │ → │ Synthesis │
│Statements │   │           │   │Statements │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
FOR presents    FOR counters    FOR summarizes  Judge decides
AGAINST presents AGAINST counters AGAINST summarizes winner
```

**Best for:** Binary decisions, exploring both sides thoroughly, devil's advocate analysis.

```
> /oxford Should we migrate to microservices or keep the monolith?
```

---

### Advocate

**Requires:** 3+ models

Devil's advocate mode. The system analyzes the emerging consensus from Phase 1-2, then designates one model (the last one) to challenge that consensus while others defend it.

**How it works:**
1. AI analyzes initial answers to identify the majority position
2. The last model becomes the "devil's advocate"
3. Advocate challenges the consensus, finding flaws and edge cases
4. Other models must defend and justify their reasoning

**Flow:**
```
Phase 1           Phase 2              Phase 3
┌─────────────┐   ┌─────────────────┐   ┌─────────────┐
│  Positions  │ → │Cross-Examination│ → │  Synthesis  │
│             │   │                 │   │             │
└─────────────┘   └─────────────────┘   └─────────────┘
Defenders state    Advocate challenges   Final verdict
their views        each defender         with analysis
```

**Best for:** Stress-testing ideas, avoiding groupthink, critical analysis, finding weaknesses.

```
> /advocate Is our authentication system secure enough?
```

---

### Socratic

**Requires:** 2+ models

Question-driven Socratic dialogue. Instead of stating positions, models take turns as the "questioner" who probes assumptions and reasoning.

**How it works:**
1. Each round, one model becomes the **Questioner**
2. The Questioner asks ONE probing question targeting a specific claim
3. All other models respond as **Respondents**
4. The Questioner role rotates each round

**Flow:**
```
Phase 1         Phase 2            Phase 3
┌───────────┐   ┌──────────────┐   ┌───────────┐
│  Thesis   │ → │   Elenchus   │ → │ Synthesis │
│           │   │  (Q&A Rounds)│   │           │
└───────────┘   └──────────────┘   └───────────┘
Respondent      Questioners probe   Refined
states view     assumptions         understanding
```

**Best for:** Deep exploration, exposing hidden assumptions, understanding complex topics, learning.

```
> /socratic What assumptions are we making about user behavior?
```

---

### Delphi

**Requires:** 3+ models

Iterative consensus-building for estimates and forecasts. Models provide independent estimates, then revise after seeing others' reasoning across multiple rounds.

**How it works:**
1. **Round 1** - Each model provides an independent estimate with confidence level
2. **Round 2** - Models see anonymized group estimates and may revise
3. **Round 3** - Final revision opportunity before aggregation
4. **Synthesis** - Aggregates final estimates into consensus range

**Flow:**
```
Phase 1         Phase 2         Phase 3         Phase 4
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│ Round 1   │ → │ Round 2   │ → │ Round 3   │ → │ Aggregate │
│ Estimates │   │ Revisions │   │ Final Rev │   │ Consensus │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
Independent     See group,      Last chance     Synthesize
estimates       may revise      to revise       final range
```

**Best for:** Time estimates, cost projections, risk assessments, quantitative forecasting.

```
> /delphi How long would it take to migrate this codebase to Python 3?
```

---

### Brainstorm

**Requires:** 2+ models

Creative ideation with three distinct phases. Models generate wild ideas without judgment, then build on each other's concepts before converging on the best options.

**How it works:**
1. **Diverge** - Generate as many ideas as possible, no criticism allowed
2. **Build** - Combine and expand on the most promising ideas from others
3. **Converge** - Evaluate and select the top 3 ideas with justification

**Flow:**
```
Phase 1         Phase 2         Phase 3         Phase 4
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│  Diverge  │ → │   Build   │ → │ Converge  │ → │ Synthesis │
│           │   │           │   │           │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
Generate wild   Combine and     Evaluate and    Present top
ideas, no       expand on       select top 3    ideas with
judgment        others' ideas   ideas           details
```

**Best for:** Creative problem-solving, feature ideation, exploring possibilities, innovation.

```
> /brainstorm How might we improve user onboarding?
```

---

### Tradeoff

**Requires:** 2+ models

Structured comparison of alternatives using explicit criteria. Models define options, establish evaluation dimensions, score each option, then synthesize a recommendation.

**How it works:**
1. **Frame** - Define the alternatives to compare
2. **Criteria** - Establish evaluation dimensions with weights
3. **Evaluate** - Score each alternative on each criterion (1-10)
4. **Synthesize** - Recommend based on weighted analysis

**Flow:**
```
Phase 1         Phase 2         Phase 3         Phase 4
┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐
│   Frame   │ → │ Criteria  │ → │ Evaluate  │ → │ Recommend │
│           │   │           │   │           │   │           │
└───────────┘   └───────────┘   └───────────┘   └───────────┘
Define the      Establish       Score each      Synthesize
alternatives    evaluation      alternative     recommendation
to compare      dimensions      (1-10 scale)    with tradeoffs
```

**Best for:** Technology choices, architecture decisions, vendor selection, A vs B comparisons.

```
> /tradeoff Should we use PostgreSQL or MongoDB for this project?
```

---

### Method Requirements Summary

| Method | Models Required | Role Assignment |
|--------|-----------------|-----------------|
| Standard | 2+ | Equal participation |
| Oxford | 2, 4, 6... (even) | FOR / AGAINST teams |
| Advocate | 3+ | 1 challenger + defenders |
| Socratic | 2+ | Rotating questioner |
| Delphi | 3+ | Anonymous panelists |
| Brainstorm | 2+ | Equal ideators |
| Tradeoff | 2+ | Equal evaluators |

---

### When to Use Each Method

Choose your method based on the type of question:

| Method | Best For | Example Questions |
|--------|----------|-------------------|
| **Standard** | Technical questions, best practices, problem-solving | "How should we handle errors?", "What architecture fits this use case?" |
| **Oxford** | Binary decisions, controversial topics, pros/cons analysis | "Motion: We should migrate to microservices", "Motion: AI should be regulated" |
| **Advocate** | Consensus-prone topics where critical thinking is needed | "Is our security good enough?", "Should we use TypeScript?" |
| **Socratic** | Philosophical questions, exploring definitions and assumptions | "What is good code?", "What assumptions are we making about users?" |
| **Delphi** | Estimates, forecasts, quantitative predictions | "How long will migration take?", "What's the project risk level?" |
| **Brainstorm** | Creative ideation, exploring possibilities, innovation | "How might we improve UX?", "What features should we add?" |
| **Tradeoff** | Technology choices, A vs B decisions, vendor selection | "PostgreSQL or MongoDB?", "AWS or GCP for this workload?" |

**Tips:**
- **Not sure?** Press **Tab** to get AI-powered method recommendations based on your question
- Use **Standard** as your default for most technical discussions
- Use **Oxford** with "Motion:" prefix to signal a formal debate proposition
- Use **Advocate** when you suspect everyone will agree too easily — it forces critical scrutiny
- Use **Socratic** when there's no clear right/wrong answer and you want to explore deeper
- Use **Delphi** when you need a numerical estimate or forecast with confidence ranges
- Use **Brainstorm** when you want creative ideas without early criticism
- Use **Tradeoff** when comparing specific alternatives with clear criteria

---

### Selecting a Method

**Via config (.env):**
```bash
QUORUM_METHOD=oxford
```

**Via command (session override):**
```
> /method oxford
✓ Method set to: oxford
```

**Via inline syntax (one-time use):**
```
> /oxford Should we use microservices or a monolith?
> /advocate Is this architecture scalable?
> /socratic What assumptions are we making?
> /delphi How long will this refactoring take?
> /brainstorm How can we improve performance?
> /tradeoff React vs Vue for this project?
```

**Via AI advisor (recommended for new users):**
Press **Tab** to analyze your question and get method recommendations.

**Note:** If you try to use a method with an incompatible number of models, Quorum will show an error:
```
> /oxford What should we do?
Error: Oxford requires an even number of models for balanced FOR/AGAINST teams
```

---

### Method Advisor

**Not sure which method to use?** Press **Tab** to get AI-powered recommendations based on your question. The Method Advisor analyzes your question and suggests the most suitable discussion method with confidence scores.

**How it works:**

1. Press **Tab** in the input field
2. Enter your question (or press Enter if already typed)
3. Review AI recommendations with confidence scores
4. Select the recommended method or choose an alternative
5. Press Esc to cancel and return to manual selection

**Example:**

```
Press Tab → Opens Method Advisor

METHOD ADVISOR
What's your question?
› How long will it take to migrate our database to PostgreSQL?

[Analyzing with gpt-5.1...]

RECOMMENDED:

● Delphi (95%)
  Best for time estimates and forecasts. Multiple models provide
  independent estimates, then revise based on group feedback to
  converge on a consensus range.

○ Tradeoff (70%)
  Could work if comparing PostgreSQL migration strategies

○ Standard (60%)
  Fallback for general technical discussion

↑↓ Navigate • Enter Select • Backspace Back • Esc Cancel
```

**Key features:**
- Uses your first validated model as the analyzer
- Returns primary recommendation plus 1-2 alternatives
- Includes confidence scores (0-100) and reasoning
- Requires at least one validated model to work
- Smart method selection based on question patterns

**Keyboard shortcuts:**
- **Tab** - Open Method Advisor
- **Enter** - Analyze question / Select method
- **↑/↓** - Navigate recommendations
- **Backspace** - Return to question input
- **Esc** - Cancel and close advisor

---

## Advanced Settings

### Synthesizer Mode

Controls which model creates the final synthesis:

| Mode | Behavior |
|------|----------|
| `first` | First selected model always synthesizes (default) |
| `random` | Random model chosen each time |
| `rotate` | Cycles through models across discussions |

```bash
# In .env
QUORUM_SYNTHESIZER=rotate
```

### Discussion Length

`QUORUM_ROUNDS_PER_AGENT` controls how many turns each model gets in the discussion phase. Higher values = longer, deeper discussions but more API costs.

| Setting | Effect |
|---------|--------|
| `1` | Quick discussions, 1 turn per model |
| `2` | Default, balanced depth |
| `3-5` | Extended discussions for complex topics |

### Response Language

By default, Quorum matches the language of your question. Use `QUORUM_DEFAULT_LANGUAGE` to force all responses in a specific language:

```bash
# Force Swedish responses
QUORUM_DEFAULT_LANGUAGE=Swedish

# Force English responses
QUORUM_DEFAULT_LANGUAGE=English
```

### Execution Mode (VRAM Optimization)

When running multiple local Ollama models, they compete for GPU VRAM which can cause crashes or slowdowns. Quorum handles this automatically:

| Mode | Behavior |
|------|----------|
| `auto` | **Default.** Cloud APIs run in parallel, Ollama runs sequentially |
| `parallel` | Always run all models simultaneously (cloud-only setups) |
| `sequential` | Always run models one at a time (safest for limited VRAM) |

```bash
# In .env (usually not needed - auto works for most users)
QUORUM_EXECUTION_MODE=auto
```

**Note:** With `auto` mode (default), you don't need to configure anything. Quorum automatically detects Ollama models and runs them sequentially to prevent VRAM competition.

### UI Language

The terminal UI is available in 6 languages, controlled by `QUORUM_DEFAULT_LANGUAGE`:

| Language | Values |
|----------|--------|
| English | `en`, `English` (default) |
| Swedish | `sv`, `Swedish`, `Svenska` |
| German | `de`, `German`, `Deutsch` |
| French | `fr`, `French`, `Francais` |
| Spanish | `es`, `Spanish`, `Espanol` |
| Italian | `it`, `Italian`, `Italiano` |

### Discussion Logging & Export

Quorum supports two ways to save discussions:

**Manual export** - Use the `/export` command to save the current discussion:

```bash
/export          # Export with default format (md)
/export md       # Markdown format
/export text     # Plain text (for social media)
/export pdf      # PDF format
/export json     # JSON format (for ML/RAG pipelines)
```

Configure default export location and format:

```bash
QUORUM_EXPORT_DIR=~/.quorum/exports   # Directory (default: home)
QUORUM_EXPORT_FORMAT=md               # Default format: md, text, pdf, json
```

| Format | Best For |
|--------|----------|
| `md` | GitHub, Discord, documentation |
| `text` | Social media, plain copy-paste |
| `pdf` | Formatted sharing, printing |
| `json` | ML training data, RAG datasets, API integrations |

**Auto-save** - All discussions are automatically saved as markdown. Configure the directory:

```bash
# Auto-save directory (default: ~/reports)
QUORUM_REPORT_DIR=~/reports
```

Files are saved as `quorum-{question}-{timestamp}.{ext}`.

## Troubleshooting

### WSL + Windows Ollama

If you run Quorum in WSL but Ollama on Windows, WSL cannot reach Windows `localhost` by default. You need to make Ollama listen on all interfaces:

**Option 1: Set environment variable before starting Ollama**
```powershell
# PowerShell (run before starting Ollama)
$env:OLLAMA_HOST = "0.0.0.0"
ollama serve
```

**Option 2: Set permanent system environment variable**
1. Open System Properties → Environment Variables
2. Add new System variable: `OLLAMA_HOST` = `0.0.0.0`
3. Restart Ollama

**Option 3: Configure Quorum to use Windows LAN IP**
```powershell
# On Windows, find your LAN IP
ipconfig | findstr "IPv4"
# Look for something like: 192.168.x.x or 10.x.x.x
```

```bash
# Add to .env in Quorum (WSL)
OLLAMA_BASE_URL=http://192.168.x.x:11434  # Use your Windows LAN IP
```

**Note:** The LAN IP may change if your router assigns a new address. Use a static IP or re-check with `ipconfig` if connection stops working.

### Ollama models not showing in /models

1. **Check Ollama is running:** `ollama list` should show your models
2. **Check connectivity:** `curl http://localhost:11434/api/tags` should return JSON
3. **WSL users with Ollama on Windows:**
   - Verify Ollama listens on 0.0.0.0: `netstat -an | findstr 11434` (on Windows)
   - Use Windows LAN IP, not the IP from `/etc/resolv.conf`
   - See [WSL + Windows Ollama](#wsl--windows-ollama) above

### "Frontend not found" or "node_modules not found"

Run the install script or manually build frontend:

```bash
cd frontend && npm install && npm run build && cd ..
```

### "No API keys configured"

Make sure you have created `.env` in the project directory with at least one API key.

### "Insufficient credits" error

Your API credits are exhausted. Add credits at:
- Anthropic: https://console.anthropic.com/settings/plans
- OpenAI: https://platform.openai.com/settings/organization/billing

### "Quorum is not installed" error

Run the install script first:
- Windows: `install.bat`
- Linux/macOS: `./install.sh`

### uv installation fails (corporate/restricted environments)

If `pip install uv` fails due to network restrictions, install uv manually:

```bash
# Alternative: download uv directly
curl -LsSf https://astral.sh/uv/install.sh | sh   # Linux/macOS
# Or on Windows PowerShell:
irm https://astral.sh/uv/install.ps1 | iex
```

Or use pip with venv manually (slower but works offline):
```bash
python -m venv .venv
.venv/bin/pip install -e .    # Linux/macOS
.venv\Scripts\pip install -e . # Windows
```

### Updating after code changes

```bash
git pull
uv sync
cd frontend && npm run build && cd ..
```

## Data Storage

Quorum stores user data in `~/.quorum/`:

- `history.json` - Input history
- `settings.json` - Saved model selections and settings
- `validated_models.json` - Cached model validations (avoids repeated API checks)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](.github/CONTRIBUTING.md) for guidelines.

## License

Business Source License 1.1 - see [LICENSE](LICENSE) for details.

**What this means:**
- Free for personal use, internal company use, and contributions
- Commercial SaaS offerings based on Quorum require a separate license
- Converts to Apache 2.0 on 2029-12-07
