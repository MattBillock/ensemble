# GitHub Bots Integration Suite - Architecture Document

## Overview
This document defines the technical architecture for the GitHub Bots Integration Suite - a set of four coordinated Python-based automation bots for streamlining Git workflows.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.9+ | Core implementation |
| Git Library | GitPython + subprocess | Git operations |
| GitHub API | PyGithub | Remote GitHub operations |
| Configuration | PyYAML | YAML config parsing |
| Scheduling | APScheduler | Job scheduling |
| Logging | Python logging | Structured logging with rotation |
| Testing | pytest + pytest-cov | Unit and integration testing |
| CLI | Click | Command-line interface |

---

## Project Structure

```
github-bots/
├── github_bots/
│   ├── __init__.py
│   ├── cli.py                 # CLI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration loader/validator
│   │   └── defaults.py        # Default configuration values
│   ├── core/
│   │   ├── __init__.py
│   │   ├── base_bot.py        # Abstract base class for all bots
│   │   ├── git_wrapper.py     # Git operations wrapper
│   │   ├── scheduler.py       # Job scheduling utilities
│   │   └── exceptions.py      # Custom exceptions
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logging_setup.py   # Logging configuration
│   │   └── validators.py      # Input validators
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── sync_bot.py        # Sync Bot implementation
│   │   ├── documentation_bot.py # Documentation Bot implementation
│   │   ├── commit_bot.py      # Commit Bot implementation
│   │   └── push_bot.py        # Push Bot implementation
│   └── orchestrator.py        # Bot coordination
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # pytest fixtures
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_git_wrapper.py
│   │   ├── test_sync_bot.py
│   │   ├── test_documentation_bot.py
│   │   ├── test_commit_bot.py
│   │   └── test_push_bot.py
│   └── integration/
│       └── test_workflow.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
└── .github-bots.yml.example
```

---

## Component Architecture

### 1. Core Layer

#### Base Bot (`core/base_bot.py`)
Abstract base class providing common functionality:
- Configuration access
- Logging interface
- Error handling
- State management
- Lifecycle hooks (init, run, cleanup)

```python
class BaseBot(ABC):
    def __init__(self, config: Config, logger: Logger)
    @abstractmethod
    def run(self) -> BotResult
    def validate_preconditions(self) -> bool
    def handle_error(self, error: Exception) -> None
```

#### Git Wrapper (`core/git_wrapper.py`)
Encapsulates all Git operations:
- Uses GitPython for structured operations
- Falls back to subprocess for edge cases
- Handles authentication transparently
- Provides consistent error handling

Key methods:
- `fetch()`, `pull()`, `rebase()`
- `stash_push()`, `stash_pop()`, `stash_list()`
- `stage()`, `commit()`, `push()`
- `get_status()`, `get_diff()`, `get_log()`

#### Configuration (`config/config.py`)
- Loads from `.github-bots.yml`
- Merges with defaults
- Validates configuration schema
- Supports environment variable overrides

### 2. Bot Layer

#### Sync Bot
- **Input**: Current working directory state
- **Output**: Synchronized branch
- **Operations**: fetch → stash → pull/rebase → unstash
- **Error Handling**: Conflict detection, safe abort

#### Documentation Bot
- **Input**: Staged changes (git diff)
- **Output**: Formatted commit message
- **Operations**: analyze diff → detect type → generate message
- **Templates**: Conventional Commits format

#### Commit Bot
- **Input**: Commit message (from Doc Bot or manual)
- **Output**: New commit
- **Operations**: validate → stage → commit → verify
- **Integration**: Signals Push Bot on success

#### Push Bot
- **Input**: Unpushed commits
- **Output**: Pushed to remote
- **Operations**: check unpushed → push → verify → retry on failure
- **Scheduling**: APScheduler cron-like intervals

### 3. Orchestrator
Coordinates bot execution:
- Manages bot lifecycle
- Handles inter-bot communication
- Provides workflow automation
- Implements retry logic

---

## Data Flow

```
[User/Trigger]
      │
      ▼
┌─────────────┐     ┌─────────────────┐
│  Sync Bot   │────▶│  Git Wrapper    │
└─────────────┘     └─────────────────┘
      │                     │
      ▼                     ▼
┌─────────────┐     ┌─────────────────┐
│  Doc Bot    │────▶│  Diff Analysis  │
└─────────────┘     └─────────────────┘
      │
      ▼
┌─────────────┐
│ Commit Bot  │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Push Bot   │
└─────────────┘
      │
      ▼
[GitHub Remote]
```

---

## Configuration Schema

```yaml
# .github-bots.yml
general:
  log_level: INFO
  log_file: ~/.github-bots/logs/bots.log

sync_bot:
  enabled: true
  strategy: rebase  # merge | rebase
  remote: origin
  auto_stash: true
  schedule: "*/30 * * * *"

documentation_bot:
  enabled: true
  format: conventional_commits
  include_scope: true
  max_subject_length: 50
  body_wrap_length: 72

commit_bot:
  enabled: true
  gpg_sign: false
  validate_message: true
  auto_stage: true

push_bot:
  enabled: true
  remote: origin
  schedule: "*/5 * * * *"
  strategy: batch  # immediate | batch | manual
  force_push: never  # never | with_lease | allowed
```

---

## Error Handling Strategy

1. **Recoverable Errors**: Retry with backoff (network issues)
2. **User Intervention Required**: Log clearly, notify user (conflicts)
3. **Fatal Errors**: Safe abort, preserve state, detailed logging

All errors produce structured logs with:
- Timestamp
- Bot identifier
- Operation attempted
- Error details
- Recovery suggestions

---

## Security Considerations

- No credentials stored in config files
- Uses system Git credential helpers
- GPG signing support optional
- All operations logged (without sensitive data)
- Respects .gitignore patterns

---

## Testing Strategy

### Unit Tests
- Each component tested in isolation
- Mocked Git operations
- >80% code coverage target

### Integration Tests
- Real Git repository operations
- Temporary repository fixtures
- End-to-end workflow validation

---

## Implementation Notes

### Milestone 1 Focus
For the foundation milestone, implement:
1. Project structure and packaging
2. Configuration system with validation
3. Git wrapper with core operations
4. Logging framework
5. Base bot class
6. Test infrastructure

This provides the foundation for all four bot implementations.
