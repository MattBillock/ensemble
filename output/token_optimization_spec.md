# Token Optimization Implementation Specification

## Overview

Implement a token optimization system to reduce API costs and improve performance by optimizing requests before sending them to the Anthropic API.

## Problem Statement

Current implementation sends full message histories and verbose system prompts to the API, which:
- Increases token costs unnecessarily
- Slows down response times
- May hit context limits for long conversations
- Wastes tokens on redundant information

## Solution

Create a `TokenOptimizer` class that intercepts and optimizes requests before API calls.

## File Structure

### New File: `src/runtime/agents/token_optimizer.py`

```python
"""Token optimization utilities for reducing API costs and improving performance."""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TokenOptimizer:
    """Optimizes token usage for API requests."""
    
    # Constants
    CHARS_PER_TOKEN = 4  # Conservative estimate
    TARGET_CONTEXT_BUDGET = 50000  # Tokens
    
    MAX_CONTEXT_TOKENS = {
        "claude-opus-4-5-20251101": 200000,
        "claude-sonnet-4-5-20250929": 200000,
        "claude-3-5-sonnet-20241022": 200000,
        "claude-3-5-haiku-20241022": 200000,
        "claude-3-haiku-20240307": 200000,
        "claude-3-opus-20240229": 200000,
        "default": 100000
    }
    
    def __init__(self, model: str = "default"):
        """Initialize TokenOptimizer."""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        pass
    
    def estimate_message_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """Estimate total tokens in a message list."""
        pass
    
    def optimize_messages(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        max_tokens: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        """
        Optimize message history and system prompt.
        
        Returns:
            (optimized_messages, optimized_system_prompt, optimization_stats)
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        pass


def get_token_optimizer(model: str = "default") -> TokenOptimizer:
    """Factory function to get TokenOptimizer instance."""
    return TokenOptimizer(model=model)
```

## Integration Points

### 1. AgentRuntime Integration

Modify `src/runtime/agents/runtime.py`:

```python
# In AgentRuntime.__init__():
from .token_optimizer import get_token_optimizer

self.token_optimizer = get_token_optimizer(model=model)

# In execute() method, before API call:
# Optimize messages and system prompt
optimized_messages, optimized_system, opt_stats = self.token_optimizer.optimize_messages(
    messages=api_kwargs["messages"],
    system_prompt=api_kwargs["system"],
    max_tokens=None  # Use default budget
)

# Log optimization results
if opt_stats["optimization_applied"]:
    logger.info(
        f"Token optimization: {opt_stats['original_tokens']} -> {opt_stats['final_tokens']} "
        f"(saved {opt_stats['tokens_saved']} tokens, {opt_stats['compression_ratio']:.2%})"
    )

# Update API kwargs with optimized values
api_kwargs["messages"] = optimized_messages
api_kwargs["system"] = optimized_system
```

### 2. Backend API Endpoints

Add to `src/field/ensemble_ui/backend/main.py`:

```python
@app.get("/api/token-optimization/stats")
async def get_token_optimization_stats():
    """Get token optimization statistics across all agents."""
    # Aggregate stats from all runtime instances
    pass

@app.get("/api/token-optimization/stats/{agent_id:path}")
async def get_agent_token_stats(agent_id: str):
    """Get token optimization stats for a specific agent."""
    pass
```

## Optimization Strategies

### 1. Message History Pruning

```python
def _prune_messages_smart(messages, max_tokens):
    """
    Keep:
    - First message (original context)
    - Last N messages (working memory)
    
    Remove/summarize:
    - Middle messages
    - Redundant tool results
    """
```

### 2. System Prompt Compression

```python
def _compress_system_prompt(system_prompt):
    """
    Remove:
    - Verbose examples
    - Detailed format specifications
    - Redundant instructions
    
    Keep:
    - Core purpose
    - Essential instructions
    - Critical output format
    """
```

### 3. Aggressive Compression

```python
def _compress_messages(messages, max_tokens):
    """
    Last resort:
    - Summarize middle conversation
    - Keep only essential context
    - Preserve most recent exchanges
    """
```

## Statistics Tracking

Track and expose:
- `total_optimizations`: Number of optimization operations
- `tokens_saved`: Total tokens saved across all optimizations
- `compression_ratio`: Average compression achieved
- `original_tokens`: Tokens before optimization
- `final_tokens`: Tokens after optimization

## Testing Strategy

### Unit Tests

Create `tests/test_token_optimizer.py`:

```python
def test_estimate_tokens():
    """Test token estimation from text."""
    pass

def test_optimize_messages_under_budget():
    """Test that messages under budget are not modified."""
    pass

def test_optimize_messages_over_budget():
    """Test that over-budget messages are optimized."""
    pass

def test_prune_messages_smart():
    """Test smart message pruning logic."""
    pass

def test_compress_system_prompt():
    """Test system prompt compression."""
    pass

def test_stats_tracking():
    """Test that stats are tracked correctly."""
    pass
```

### Integration Tests

```python
def test_runtime_integration():
    """Test TokenOptimizer integration with AgentRuntime."""
    pass

def test_api_endpoint():
    """Test token optimization stats API endpoint."""
    pass
```

## Success Metrics

- [ ] Token usage reduced by at least 30% on average
- [ ] No degradation in agent performance
- [ ] Stats accurately tracked and exposed via API
- [ ] All tests pass
- [ ] Documentation complete

## Implementation Checklist

- [ ] Create `token_optimizer.py` module
- [ ] Implement `TokenOptimizer` class with all methods
- [ ] Integrate into `AgentRuntime`
- [ ] Add API endpoints for stats
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Monitor performance in production

## Dependencies

- No external dependencies required
- Uses existing logging infrastructure
- Compatible with current AgentRuntime architecture

## Rollout Plan

1. Implement `TokenOptimizer` class
2. Add unit tests and verify functionality
3. Integrate into `AgentRuntime` with feature flag
4. Test with sample agents
5. Monitor token usage reduction
6. Enable by default if successful
7. Add monitoring dashboard

## Performance Considerations

- Token estimation is fast (string length calculation)
- Message pruning is O(n) where n = message count
- System prompt compression is O(m) where m = prompt length
- Minimal overhead added to API call preparation

## Future Enhancements

- Use actual tokenizer for precise counts (tiktoken library)
- ML-based importance scoring for message retention
- Adaptive budget based on task complexity
- Token budget allocation across agent swarms
- Real-time optimization monitoring dashboard
