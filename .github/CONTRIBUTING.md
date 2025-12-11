# Contributing to Quorum

Thank you for your interest in contributing to Quorum! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

If you find a bug, please [open an issue](https://github.com/Detrol/quorum-cli/issues/new?template=bug_report.yml) with:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, Quorum version)

### Suggesting Features

We welcome feature suggestions! Please [open a feature request](https://github.com/Detrol/quorum-cli/issues/new?template=feature_request.yml) with:

- A clear description of the problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/quorum.git
cd quorum

# Run the install script
./install.sh

# Create .env with your API keys (for live testing)
cp .env.example .env
# Edit .env with your keys

# Run tests
pytest                          # Unit tests (no API keys needed)
pytest tests/test_live.py -v    # Live tests (requires API keys)
```

## Code Style

- We use [ruff](https://github.com/astral-sh/ruff) for linting
- Run `uvx ruff check src/` before submitting PRs (or `uvx ruff check src/ --fix` to auto-fix)
- Follow existing code patterns and naming conventions
- Add type hints where possible
- Write docstrings for public functions

## Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PR
- Unit tests should not require API keys (use mocking)
- Live/integration tests should be marked with `@pytest.mark.live`

### Running Tests

```bash
# Run all unit tests (no API keys needed)
pytest tests/ -v -m "not live"

# Run specific test file
pytest tests/test_agents.py -v

# Run live tests (requires API keys)
pytest tests/test_live.py -v
```

## Project Structure

```
quorum/
├── src/quorum/          # Main source code
│   ├── agents.py        # Prompt templates and method logic
│   ├── config.py        # Settings and configuration
│   ├── ipc.py           # JSON-RPC communication
│   ├── models.py        # Model client factory
│   ├── providers.py     # Provider detection
│   └── team.py          # Main orchestration
├── frontend/            # React/Ink terminal UI
│   ├── src/
│   │   ├── components/  # UI components
│   │   ├── ipc/         # IPC client and protocol types
│   │   └── store/       # Zustand state management
├── tests/               # Test suite
├── docs/                # Documentation
│   └── api/             # API specifications
└── examples/            # Integration examples
```

## Architecture Overview

Quorum uses a **split architecture** with a Python backend and React/Ink frontend communicating via JSON-RPC over stdin/stdout.

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React/Ink)                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   UI     │ →  │  Store   │ →  │   IPC    │ →  │  stdin   │  │
│  │Components│ ←  │ (Zustand)│ ←  │  Client  │ ←  │  stdout  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ JSON-RPC (NDJSON)
┌─────────────────────────────────────────────────────────────────┐
│                         Backend (Python)                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   IPC    │ →  │   Team   │ →  │  Models  │ →  │    AI    │  │
│  │ Handler  │ ←  │Orchestr. │ ←  │  Client  │ ←  │   APIs   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### Backend (`src/quorum/`)

| Component | Responsibility |
|-----------|----------------|
| `ipc.py` | JSON-RPC request handling, event emission, input validation |
| `team.py` | Discussion orchestration, phase management, method flows |
| `agents.py` | Prompt templates, method requirements, role assignments |
| `models.py` | Model client factory, connection pooling, validation |
| `providers.py` | Provider detection from model ID prefix |
| `config.py` | Settings from .env, user preferences, cache management |

#### Frontend (`frontend/src/`)

| Component | Responsibility |
|-----------|----------------|
| `ipc/client.ts` | Spawns backend, handles JSON-RPC communication |
| `ipc/protocol.ts` | TypeScript types for IPC messages |
| `store/index.ts` | Zustand state management |
| `components/*.tsx` | React/Ink UI components |

### Message Types

The backend emits typed messages during discussion:

| Message Type | Description |
|--------------|-------------|
| `PhaseMarker` | Phase transitions |
| `IndependentAnswer` | Phase 1 responses |
| `CritiqueResponse` | Phase 2 structured critiques |
| `TeamTextMessage` | Discussion messages with role/round metadata |
| `FinalPosition` | Phase 4 positions with confidence |
| `SynthesisResult` | Final synthesis with consensus status |
| `ThinkingIndicator` | Model is generating response |

### Discussion Flow

```
1. Frontend sends run_discussion request
2. Backend creates FourPhaseConsensusTeam
3. Team.run_stream() yields messages:
   ├── PhaseMarker (phase 1)
   ├── IndependentAnswer (each model)
   ├── PhaseMarker (phase 2)
   ├── CritiqueResponse (each model)
   ├── ... (method-specific phases)
   └── SynthesisResult
4. IPC handler converts to events
5. Frontend updates UI via store
```

### Adding New Functionality

#### Adding a Provider

1. Add detection pattern in `providers.py`
2. Add client factory case in `models.py`
3. Add settings in `config.py`
4. Update `.env.example`

#### Adding a Discussion Method

See [docs/tutorials/ADDING_A_METHOD.md](../docs/tutorials/ADDING_A_METHOD.md)

#### Adding an IPC Method

1. Add handler in `ipc.py` handler_map
2. Add TypeScript types in `protocol.ts`
3. Add client method in `client.ts`
4. Update `docs/api/IPC_PROTOCOL.md`

### Protocol Versioning

The IPC protocol uses semantic versioning. When making changes:

- **PATCH**: Bug fixes, documentation
- **MINOR**: New methods/events (backward compatible)
- **MAJOR**: Breaking changes to existing methods/events

Update `PROTOCOL_VERSION` in both:
- `src/quorum/ipc.py`
- `frontend/src/ipc/protocol.ts`

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Reference issues when applicable (`Fixes #123`)

## Questions?

Feel free to open a [Discussion](https://github.com/Detrol/quorum-cli/discussions) for questions or ideas that don't fit into issues.

## License

By contributing, you agree that your contributions will be licensed under the project's [Business Source License 1.1](../LICENSE).
