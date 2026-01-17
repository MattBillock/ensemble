# Local Claude Integration - Architecture Design

## 1. Architecture Overview

This architecture adds support for a local Claude CLI instance as an alternative AI provider that takes priority over the Anthropic API. The design follows the existing provider system in `model_router.py` and integrates seamlessly with the current `runtime.py` execution flow.

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AgentRuntime                                 │
│                                                                      │
│  1. Receives execution request                                       │
│  2. Calls ModelRouter.select_model() with local_first=True          │
│  3. ModelRouter checks LocalClaudeProvider health                    │
│  4. If healthy → route to LocalClaudeProvider                       │
│  5. If unhealthy → fallback to Anthropic API                        │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ModelRouter                                  │
│                                                                      │
│  - Maintains LocalClaudeProvider instance                           │
│  - Health check before routing to local                             │
│  - Circuit breaker pattern for failure tracking                     │
│  - Automatic fallback on local failure                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│   LocalClaudeProvider    │   │     Anthropic API        │
│                          │   │                          │
│  - Subprocess execution  │   │  - Current implementation│
│  - JSON response parsing │   │  - Full feature set      │
│  - Health checking       │   │  - Streaming support     │
│  - Circuit breaker       │   │                          │
└──────────────────────────┘   └──────────────────────────┘
```

## 2. Component Design

### 2.1 LocalClaudeProvider (New File)

**Location**: `src/runtime/agents/local_claude_provider.py`

```python
class LocalClaudeProvider:
    """
    Executes prompts via local Claude CLI.
    
    Features:
    - CLI subprocess execution with timeout
    - JSON response parsing
    - Health checking with circuit breaker
    - Token and cost tracking from CLI output
    """
    
    def __init__(
        self,
        cli_path: str = "/opt/homebrew/bin/claude",
        timeout_seconds: int = 120,
        failure_threshold: int = 3,
        cooldown_seconds: int = 60
    ):
        self.cli_path = cli_path
        self.timeout = timeout_seconds
        self.circuit_breaker = LocalCircuitBreaker(
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds
        )
    
    def is_available(self) -> bool:
        """Check if CLI is installed and executable."""
        
    def is_healthy(self) -> bool:
        """Check circuit breaker state and CLI availability."""
        
    def execute(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "sonnet"
    ) -> LocalExecutionResult:
        """Execute prompt via CLI and return parsed result."""
```

**Key Design Decisions**:
1. Use subprocess for CLI execution (no SDK dependency)
2. Use `--print` mode for synchronous responses
3. Use `--output-format json` for structured parsing
4. Use temp file for long prompts to avoid CLI argument limits
5. Independent circuit breaker from API circuit breaker

### 2.2 LocalCircuitBreaker (in local_claude_provider.py)

```python
class LocalCircuitBreaker:
    """
    Tracks consecutive failures and implements cooldown.
    
    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Cooldown expired, allow single test request
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        cooldown_seconds: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
```

### 2.3 LocalExecutionResult (in local_claude_provider.py)

```python
@dataclass
class LocalExecutionResult:
    """Result from local CLI execution."""
    success: bool
    result_text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    duration_ms: int
    error: Optional[str] = None
    raw_response: Optional[Dict] = None
```

### 2.4 Model Router Modifications

**Location**: `src/runtime/agents/model_router.py`

**Changes**:
1. Add `LocalClaudeProvider` instance
2. Add `local_first` configuration option
3. Modify `select_model()` to check local provider first
4. Add `execute_with_local()` method for local execution

```python
class ModelRouter:
    def __init__(
        self,
        ...,
        enable_local: bool = True,  # NEW
        local_cli_path: str = "/opt/homebrew/bin/claude"  # NEW
    ):
        # ... existing init ...
        
        # NEW: Initialize local provider
        self.local_provider = LocalClaudeProvider(cli_path=local_cli_path)
        self.enable_local = enable_local
    
    def _check_local_model(self, model_id: str) -> bool:
        """MODIFIED: Actually check local availability."""
        if not self.enable_local:
            return False
        return self.local_provider.is_healthy()
    
    def should_use_local(self) -> bool:
        """NEW: Determine if local provider should be used."""
        return self.enable_local and self.local_provider.is_healthy()
    
    def execute_locally(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "sonnet"
    ) -> LocalExecutionResult:
        """NEW: Execute via local provider with fallback handling."""
```

### 2.5 Runtime Integration

**Location**: `src/runtime/agents/runtime.py`

**Changes**:
1. Check `model_router.should_use_local()` before API call
2. If local → call `model_router.execute_locally()`
3. If local fails → automatic fallback to API
4. Track provider used in activity/metrics

```python
class AgentRuntime:
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # ... existing setup ...
        
        # NEW: Provider selection
        router = self.get_model_router(self.api_key)
        use_local = router.should_use_local()
        
        # Record provider choice
        provider_used = "local" if use_local else "api"
        
        if use_local:
            try:
                result = router.execute_locally(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    model=self._map_model_to_local(model)
                )
                # Convert LocalExecutionResult to API-compatible format
                response = self._convert_local_response(result)
            except LocalExecutionError:
                # Fallback to API
                logger.warning("Local execution failed, falling back to API")
                use_local = False
                provider_used = "api_fallback"
        
        if not use_local:
            # Existing API execution path
            response = self.client.messages.create(...)
```

### 2.6 Activity Tracker Enhancement

**Location**: `src/runtime/agents/activity_tracker.py`

**Changes**:
1. Add `provider` field to execution records
2. Track local vs API usage statistics

```python
def record_agent_completed(
    self,
    ...,
    provider: str = "api"  # NEW: "local", "api", or "api_fallback"
):
    record["provider"] = provider
```

## 3. CLI Execution Details

### 3.1 Command Format

```bash
# Basic execution
/opt/homebrew/bin/claude --print --output-format json "prompt text"

# With system prompt
/opt/homebrew/bin/claude --print --output-format json --system-prompt "system prompt" "prompt text"

# With model selection
/opt/homebrew/bin/claude --print --output-format json --model sonnet "prompt text"

# Full command
/opt/homebrew/bin/claude \
    --print \
    --output-format json \
    --model sonnet \
    --system-prompt "You are a helpful assistant" \
    "User's prompt here"
```

### 3.2 Long Prompt Handling

For prompts exceeding ~100KB (CLI argument limits):

```python
def _execute_with_temp_file(self, prompt: str, ...) -> subprocess.CompletedProcess:
    """Use temp file for long prompts."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        temp_path = f.name
    
    try:
        # Use cat to pipe content
        cmd = f"cat {temp_path} | {self.cli_path} --print --output-format json ..."
        return subprocess.run(cmd, shell=True, capture_output=True, timeout=self.timeout)
    finally:
        os.unlink(temp_path)
```

### 3.3 JSON Response Parsing

Expected CLI output format:

```json
{
  "type": "result",
  "result": "The response text from Claude...",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 250
  },
  "total_cost_usd": 0.0012
}
```

Parsing strategy:

```python
def _parse_cli_output(self, stdout: str) -> LocalExecutionResult:
    data = json.loads(stdout)
    return LocalExecutionResult(
        success=True,
        result_text=data.get("result", ""),
        input_tokens=data.get("usage", {}).get("input_tokens", 0),
        output_tokens=data.get("usage", {}).get("output_tokens", 0),
        cost_usd=data.get("total_cost_usd", 0.0),
        duration_ms=...,
        raw_response=data
    )
```

## 4. Configuration

### 4.1 Environment Variables

```bash
# Enable/disable local provider
ENSEMBLE_LOCAL_CLAUDE_ENABLED=true

# CLI path (default: /opt/homebrew/bin/claude)
ENSEMBLE_LOCAL_CLAUDE_PATH=/opt/homebrew/bin/claude

# Timeout in seconds (default: 120)
ENSEMBLE_LOCAL_CLAUDE_TIMEOUT=120

# Circuit breaker settings
ENSEMBLE_LOCAL_FAILURE_THRESHOLD=3
ENSEMBLE_LOCAL_COOLDOWN_SECONDS=60
```

### 4.2 Runtime Configuration

```python
router = ModelRouter(
    anthropic_key=api_key,
    enable_local=True,
    local_cli_path="/opt/homebrew/bin/claude"
)
```

## 5. Error Handling

### 5.1 Error Types

| Error | Handling | Recovery |
|-------|----------|----------|
| CLI not found | Mark unhealthy, fallback to API | Manual install required |
| Subprocess timeout | Record failure, fallback | Circuit breaker cooldown |
| JSON parse error | Log warning, treat as failure | Retry or fallback |
| CLI exit code != 0 | Record failure, fallback | Circuit breaker cooldown |
| Permission denied | Mark unhealthy, fallback | Manual fix required |

### 5.2 Logging

```python
# On local execution attempt
logger.info(f"Attempting local execution: model={model}, prompt_length={len(prompt)}")

# On success
logger.info(f"Local execution succeeded: tokens={input+output}, cost=${cost:.4f}")

# On failure with fallback
logger.warning(f"Local execution failed ({error}), falling back to API")

# On circuit breaker open
logger.warning(f"Local provider circuit breaker open, using API directly")
```

## 6. Testing Strategy

### 6.1 Unit Tests

1. **LocalClaudeProvider tests**
   - Mock subprocess for CLI simulation
   - Test JSON parsing with various response formats
   - Test timeout handling
   - Test circuit breaker state transitions

2. **ModelRouter integration tests**
   - Test `should_use_local()` logic
   - Test fallback behavior
   - Test configuration options

### 6.2 Integration Tests

1. **End-to-end local execution**
   - Requires actual CLI installed
   - Mark as `@pytest.mark.skipif(not cli_available)`

2. **Fallback scenarios**
   - Simulate CLI failure, verify API takeover
   - Verify metrics record correct provider

## 7. Migration Path

### 7.1 Rollout Strategy

1. **Phase 1**: Add LocalClaudeProvider (no integration)
2. **Phase 2**: Add ModelRouter integration (disabled by default)
3. **Phase 3**: Enable for specific agents/tiers
4. **Phase 4**: Enable by default with API fallback

### 7.2 Backward Compatibility

- All changes are additive
- Default behavior unchanged (API-only)
- Existing tests continue to pass
- No breaking changes to public interfaces

## 8. File Summary

### New Files
- `src/runtime/agents/local_claude_provider.py`

### Modified Files
- `src/runtime/agents/model_router.py`
- `src/runtime/agents/runtime.py`
- `src/runtime/agents/activity_tracker.py`

### New Test Files
- `tests/test_local_claude_provider.py`
- `tests/test_model_router_local.py`
