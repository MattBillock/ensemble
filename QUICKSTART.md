# Ensemble Quick Start Guide

## First Time Setup

Your `.zshrc` already sources the ensemble aliases. Just reload your shell:

```bash
source ~/.zshrc
```

Or open a new terminal window.

## Available Commands

Type `ens-help` to see all available commands. Here are the most common:

### Essential Commands

```bash
# Restart everything (after code changes)
ens-restart

# Watch the logs
ens-logs

# Stop everything
ens-stop

# Check what's running
ens-status
```

### Navigation

```bash
ens      # Go to ensemble root directory
ensfr    # Go to frontend directory
ensbe    # Go to backend directory
```

### Development

```bash
# Run tests
ens-test

# Open in browser
ens-open      # Frontend UI
ens-api       # API docs

# Git operations
ens-git       # Git status
ens-push      # Add, commit, push all changes
```

## Service URLs

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## Logs Location

- `logs/backend.log` - Backend server logs
- `logs/frontend.log` - Frontend dev server logs

## Quick Workflow

```bash
# Start
ens-restart

# Watch logs in another terminal
ens-logs

# Make changes, test, commit
ens-test
ens-push

# Stop
ens-stop
```

For full documentation, see the detailed guide in the file.
