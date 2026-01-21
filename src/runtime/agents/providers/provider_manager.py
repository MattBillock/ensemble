"""
Provider Manager - Intelligent multi-provider orchestration with failover.

Manages multiple LLM providers and implements intelligent routing based on:
- Cost tracking and budget limits
- Error rates and provider health
- Provider capabilities and preferences
- Automatic failover on errors
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .base import (
    LLMProvider,
    ProviderType,
    ProviderResponse,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    ConnectionError,
    ContextLengthError,
    ToolDefinition,
)
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider
from .local_claude_provider import LocalClaudeProvider
from .ollama_provider import OllamaProvider
from .chatgpt_app_provider import ChatGPTAppProvider

logger = logging.getLogger(__name__)


class FailoverReason(Enum):
    """Reasons for failing over to another provider."""
    RATE_LIMIT = "rate_limit"
    COST_EXCEEDED = "cost_exceeded"
    ERROR_THRESHOLD = "error_threshold"
    PROVIDER_DOWN = "provider_down"
    CONTEXT_LENGTH = "context_length"
    MANUAL = "manual"


@dataclass
class ProviderHealth:
    """Health status of a provider."""
    provider_type: ProviderType
    is_healthy: bool = True
    consecutive_errors: int = 0
    last_error_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    cooldown_until: Optional[datetime] = None
    total_cost_today: float = 0.0
    requests_today: int = 0
    error_rate_1h: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    provider_type: ProviderType
    priority: int = 0  # Lower is higher priority
    daily_cost_limit: float = 100.0  # USD
    error_threshold: int = 5  # Consecutive errors before cooldown
    cooldown_seconds: int = 300  # 5 minutes
    enabled: bool = True


@dataclass
class FailoverEvent:
    """Record of a failover event."""
    timestamp: str
    from_provider: ProviderType
    to_provider: ProviderType
    reason: FailoverReason
    error_message: Optional[str] = None


class ProviderManager:
    """
    Manages multiple LLM providers with intelligent routing and failover.

    Features:
    - Automatic provider initialization
    - Cost tracking with daily limits
    - Error rate monitoring
    - Intelligent failover on failures
    - Provider health tracking
    - Cooldown periods for failing providers
    """

    def __init__(
        self,
        anthropic_key: Optional[str] = None,
        openai_key: Optional[str] = None,
        local_openai_url: Optional[str] = None,
        ollama_host: Optional[str] = None,
        claude_cli_path: Optional[str] = None,
        enable_chatgpt_app: bool = True,
        default_provider: ProviderType = ProviderType.ANTHROPIC,
        enable_failover: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize the provider manager.

        Args:
            anthropic_key: Anthropic API key
            openai_key: OpenAI API key
            local_openai_url: Local OpenAI-compatible server URL (e.g., LM Studio at
                             "http://localhost:1234/v1")
            ollama_host: Ollama API host URL
            claude_cli_path: Path to Claude CLI executable
            enable_chatgpt_app: Whether to enable ChatGPT macOS app provider
            default_provider: Default provider to use
            enable_failover: Whether to enable automatic failover
            max_retries: Maximum retries per request
        """
        self.default_provider = default_provider
        self.enable_failover = enable_failover
        self.max_retries = max_retries

        # Initialize providers
        self.providers: Dict[ProviderType, LLMProvider] = {}
        self.provider_configs: Dict[ProviderType, ProviderConfig] = {}
        self.provider_health: Dict[ProviderType, ProviderHealth] = {}

        self._lock = threading.Lock()
        self._failover_history: List[FailoverEvent] = []

        # Initialize each provider
        self._init_anthropic(anthropic_key)
        self._init_openai(openai_key)
        self._init_local_openai(local_openai_url)
        self._init_ollama(ollama_host)
        self._init_local_claude(claude_cli_path)
        if enable_chatgpt_app:
            self._init_chatgpt_app()

        # Set default priorities based on cost/quality
        self._set_default_priorities()

        logger.info(f"Provider manager initialized with {len([p for p in self.providers.values() if p.is_available])} available providers")

    def _init_anthropic(self, api_key: Optional[str]):
        """Initialize Anthropic provider."""
        provider = AnthropicProvider(api_key=api_key)
        if provider.initialize():
            self.providers[ProviderType.ANTHROPIC] = provider
            self.provider_configs[ProviderType.ANTHROPIC] = ProviderConfig(
                provider_type=ProviderType.ANTHROPIC,
                priority=1,  # High priority - best quality
                daily_cost_limit=50.0
            )
            self.provider_health[ProviderType.ANTHROPIC] = ProviderHealth(
                provider_type=ProviderType.ANTHROPIC
            )

    def _init_openai(self, api_key: Optional[str]):
        """Initialize OpenAI provider."""
        provider = OpenAIProvider(api_key=api_key)
        if provider.initialize():
            self.providers[ProviderType.OPENAI] = provider
            self.provider_configs[ProviderType.OPENAI] = ProviderConfig(
                provider_type=ProviderType.OPENAI,
                priority=2,  # Secondary - good backup
                daily_cost_limit=50.0
            )
            self.provider_health[ProviderType.OPENAI] = ProviderHealth(
                provider_type=ProviderType.OPENAI
            )

    def _init_local_openai(self, base_url: Optional[str]):
        """Initialize local OpenAI-compatible provider (LM Studio, LocalAI, vLLM, etc.)."""
        if not base_url:
            # Check common default ports for local servers
            import os
            base_url = os.environ.get("LOCAL_OPENAI_URL")
            if not base_url:
                # Try common default ports
                common_ports = [
                    "http://localhost:1234/v1",  # LM Studio
                    "http://localhost:8080/v1",  # LocalAI
                    "http://localhost:5000/v1",  # text-generation-webui
                ]
                for url in common_ports:
                    try:
                        import urllib.request
                        urllib.request.urlopen(url.replace("/v1", "/health"), timeout=1)
                        base_url = url
                        break
                    except Exception:
                        continue

        if base_url:
            provider = OpenAIProvider(
                api_key="not-needed",  # Local servers often don't need a key
                base_url=base_url,
                is_local=True
            )
            if provider.initialize():
                self.providers[ProviderType.LOCAL_OPENAI] = provider
                self.provider_configs[ProviderType.LOCAL_OPENAI] = ProviderConfig(
                    provider_type=ProviderType.LOCAL_OPENAI,
                    priority=3,  # Lower than cloud providers
                    daily_cost_limit=float('inf')  # No cost
                )
                self.provider_health[ProviderType.LOCAL_OPENAI] = ProviderHealth(
                    provider_type=ProviderType.LOCAL_OPENAI
                )

    def _init_ollama(self, host: Optional[str]):
        """Initialize Ollama provider."""
        provider = OllamaProvider(host=host)
        if provider.initialize():
            self.providers[ProviderType.OLLAMA] = provider
            self.provider_configs[ProviderType.OLLAMA] = ProviderConfig(
                provider_type=ProviderType.OLLAMA,
                priority=3,  # Lower priority - free but less capable
                daily_cost_limit=float('inf')  # No cost
            )
            self.provider_health[ProviderType.OLLAMA] = ProviderHealth(
                provider_type=ProviderType.OLLAMA
            )

    def _init_local_claude(self, cli_path: Optional[str]):
        """Initialize local Claude provider."""
        provider = LocalClaudeProvider(cli_path=cli_path)
        if provider.initialize():
            self.providers[ProviderType.LOCAL_CLAUDE] = provider
            self.provider_configs[ProviderType.LOCAL_CLAUDE] = ProviderConfig(
                provider_type=ProviderType.LOCAL_CLAUDE,
                priority=2,  # Same as OpenAI - Claude quality
                daily_cost_limit=float('inf')  # No direct API cost
            )
            self.provider_health[ProviderType.LOCAL_CLAUDE] = ProviderHealth(
                provider_type=ProviderType.LOCAL_CLAUDE
            )

    def _init_chatgpt_app(self):
        """Initialize ChatGPT macOS app provider."""
        provider = ChatGPTAppProvider()
        if provider.initialize():
            self.providers[ProviderType.CHATGPT_APP] = provider
            self.provider_configs[ProviderType.CHATGPT_APP] = ProviderConfig(
                provider_type=ProviderType.CHATGPT_APP,
                priority=4,  # Lower priority - requires macOS and app installed
                daily_cost_limit=float('inf')  # ChatGPT Plus subscription, no per-call cost
            )
            self.provider_health[ProviderType.CHATGPT_APP] = ProviderHealth(
                provider_type=ProviderType.CHATGPT_APP
            )

    def _set_default_priorities(self):
        """Set default provider priorities."""
        # Priority order: Anthropic > Local Claude > OpenAI > ChatGPT App > Local OpenAI > Ollama
        # Cloud providers first (better quality), then local (cost savings/privacy)
        priority_order = [
            ProviderType.ANTHROPIC,
            ProviderType.LOCAL_CLAUDE,
            ProviderType.OPENAI,
            ProviderType.CHATGPT_APP,
            ProviderType.LOCAL_OPENAI,
            ProviderType.OLLAMA
        ]

        for idx, provider_type in enumerate(priority_order):
            if provider_type in self.provider_configs:
                self.provider_configs[provider_type].priority = idx

    def send_message(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        system_prompt: Optional[str] = None,
        tools: Optional[List[ToolDefinition]] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        preferred_provider: Optional[ProviderType] = None,
        **kwargs
    ) -> ProviderResponse:
        """
        Send a message with automatic provider selection and failover.

        Args:
            messages: List of message dicts
            model: Model identifier (may be mapped to provider-specific model)
            system_prompt: Optional system prompt
            tools: Optional tool definitions
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            preferred_provider: Preferred provider to try first
            **kwargs: Additional provider-specific options

        Returns:
            ProviderResponse from the successful provider

        Raises:
            ProviderError: If all providers fail
        """
        # Determine provider order
        providers_to_try = self._get_provider_order(preferred_provider)

        if not providers_to_try:
            raise ProviderError(
                "No providers available",
                self.default_provider,
                retryable=False
            )

        last_error: Optional[ProviderError] = None

        for attempt in range(self.max_retries):
            for provider_type in providers_to_try:
                provider = self.providers.get(provider_type)
                if not provider or not self._is_provider_available(provider_type):
                    continue

                # Map model to provider-specific model
                mapped_model = self._map_model(model, provider_type)

                try:
                    response = provider.send_message(
                        messages=messages,
                        model=mapped_model,
                        system_prompt=system_prompt,
                        tools=tools,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs
                    )

                    # Success - update health
                    self._record_success(provider_type, response)
                    return response

                except RateLimitError as e:
                    last_error = e
                    self._record_error(provider_type, e, FailoverReason.RATE_LIMIT)
                    logger.warning(f"Rate limit on {provider_type.value}, trying next provider")
                    continue

                except ContextLengthError as e:
                    last_error = e
                    self._record_error(provider_type, e, FailoverReason.CONTEXT_LENGTH)
                    # Context length errors should try smaller model, not just failover
                    logger.warning(f"Context length exceeded on {provider_type.value}")
                    continue

                except ConnectionError as e:
                    last_error = e
                    self._record_error(provider_type, e, FailoverReason.PROVIDER_DOWN)
                    logger.warning(f"Connection error on {provider_type.value}, trying next")
                    continue

                except AuthenticationError as e:
                    last_error = e
                    self._record_error(provider_type, e, FailoverReason.ERROR_THRESHOLD)
                    # Auth errors won't recover - skip this provider
                    logger.error(f"Authentication failed on {provider_type.value}")
                    self._disable_provider(provider_type)
                    continue

                except ProviderError as e:
                    last_error = e
                    self._record_error(provider_type, e, FailoverReason.ERROR_THRESHOLD)
                    if e.retryable:
                        logger.warning(f"Retryable error on {provider_type.value}: {e}")
                        continue
                    else:
                        logger.error(f"Non-retryable error on {provider_type.value}: {e}")
                        continue

        # All providers failed
        raise last_error or ProviderError(
            "All providers failed",
            self.default_provider,
            retryable=False
        )

    def _get_provider_order(
        self,
        preferred: Optional[ProviderType]
    ) -> List[ProviderType]:
        """Get ordered list of providers to try."""
        available = [
            pt for pt in self.providers.keys()
            if self._is_provider_available(pt)
        ]

        if not available:
            return []

        # Sort by priority
        available.sort(key=lambda pt: self.provider_configs.get(pt, ProviderConfig(pt)).priority)

        # Move preferred to front if specified
        if preferred and preferred in available:
            available.remove(preferred)
            available.insert(0, preferred)

        return available

    def _is_provider_available(self, provider_type: ProviderType) -> bool:
        """Check if a provider is available for use."""
        if provider_type not in self.providers:
            return False

        provider = self.providers[provider_type]
        if not provider.is_available:
            return False

        config = self.provider_configs.get(provider_type)
        if config and not config.enabled:
            return False

        health = self.provider_health.get(provider_type)
        if health:
            # Check cooldown
            if health.cooldown_until and datetime.now() < health.cooldown_until:
                return False

            # Check daily cost limit
            if health.total_cost_today >= config.daily_cost_limit:
                return False

        return True

    def _map_model(self, model: str, provider_type: ProviderType) -> str:
        """Map a model name to provider-specific model."""
        # Model mapping table
        model_map = {
            ProviderType.ANTHROPIC: {
                "gpt-4o": "claude-sonnet-4-20250514",
                "gpt-4": "claude-sonnet-4-20250514",
                "gpt-3.5-turbo": "claude-3-5-haiku-20241022",
                "llama3": "claude-3-5-haiku-20241022",
            },
            ProviderType.OPENAI: {
                "claude-opus-4-5-20251101": "gpt-4o",
                "claude-sonnet-4-20250514": "gpt-4o",
                "claude-3-5-haiku-20241022": "gpt-4o-mini",
                "llama3": "gpt-4o-mini",
            },
            ProviderType.LOCAL_OPENAI: {
                # Local OpenAI-compatible servers typically use their own model names
                # These may need adjustment based on the specific server and loaded models
                "claude-opus-4-5-20251101": "gpt-4",  # or model loaded in LM Studio
                "claude-sonnet-4-20250514": "gpt-4",
                "claude-3-5-haiku-20241022": "gpt-3.5-turbo",
                "gpt-4o": "gpt-4",
                # Many local servers use llama-based models
                "llama3": "llama3",
            },
            ProviderType.OLLAMA: {
                "claude-opus-4-5-20251101": "llama3:70b",
                "claude-sonnet-4-20250514": "llama3:8b",
                "claude-3-5-haiku-20241022": "llama3:8b",
                "gpt-4o": "llama3:70b",
                "gpt-4": "llama3:70b",
            },
            ProviderType.LOCAL_CLAUDE: {
                # Local Claude uses whatever model is configured
                "gpt-4o": "claude-local",
                "llama3": "claude-local",
            },
            ProviderType.CHATGPT_APP: {
                # ChatGPT app uses whatever model is selected in the app settings
                # All models map to the generic chatgpt-app identifier
                "claude-opus-4-5-20251101": "chatgpt-app",
                "claude-sonnet-4-20250514": "chatgpt-app",
                "claude-3-5-haiku-20241022": "chatgpt-app",
                "gpt-4o": "chatgpt-app",
                "llama3": "chatgpt-app",
            }
        }

        provider_map = model_map.get(provider_type, {})
        return provider_map.get(model, model)

    def _record_success(self, provider_type: ProviderType, response: ProviderResponse):
        """Record a successful API call."""
        with self._lock:
            health = self.provider_health.get(provider_type)
            if health:
                health.is_healthy = True
                health.consecutive_errors = 0
                health.last_success_time = datetime.now()
                health.requests_today += 1

                # Update cost
                provider = self.providers.get(provider_type)
                if provider:
                    cost = provider.estimate_cost(
                        response.usage.input_tokens,
                        response.usage.output_tokens,
                        response.model
                    )
                    health.total_cost_today += cost

    def _record_error(
        self,
        provider_type: ProviderType,
        error: ProviderError,
        reason: FailoverReason
    ):
        """Record a failed API call and potentially trigger cooldown."""
        with self._lock:
            health = self.provider_health.get(provider_type)
            if health:
                health.consecutive_errors += 1
                health.last_error_time = datetime.now()

                # Calculate error rate
                total = health.requests_today + health.consecutive_errors
                if total > 0:
                    health.error_rate_1h = health.consecutive_errors / total

                # Check if cooldown should be triggered
                config = self.provider_configs.get(provider_type)
                if config and health.consecutive_errors >= config.error_threshold:
                    health.is_healthy = False
                    health.cooldown_until = datetime.now() + timedelta(seconds=config.cooldown_seconds)
                    logger.warning(
                        f"Provider {provider_type.value} in cooldown until {health.cooldown_until}"
                    )

            # Record failover event
            if self.enable_failover:
                next_provider = self._get_next_provider(provider_type)
                if next_provider:
                    self._failover_history.append(FailoverEvent(
                        timestamp=datetime.now().isoformat(),
                        from_provider=provider_type,
                        to_provider=next_provider,
                        reason=reason,
                        error_message=str(error)
                    ))

    def _get_next_provider(self, current: ProviderType) -> Optional[ProviderType]:
        """Get the next provider in failover order."""
        order = self._get_provider_order(None)
        try:
            idx = order.index(current)
            if idx + 1 < len(order):
                return order[idx + 1]
        except ValueError:
            pass
        return order[0] if order else None

    def _disable_provider(self, provider_type: ProviderType):
        """Disable a provider (e.g., due to auth failure)."""
        config = self.provider_configs.get(provider_type)
        if config:
            config.enabled = False
            logger.warning(f"Provider {provider_type.value} has been disabled")

    def set_daily_cost_limit(self, provider_type: ProviderType, limit: float):
        """Set the daily cost limit for a provider."""
        config = self.provider_configs.get(provider_type)
        if config:
            config.daily_cost_limit = limit
            logger.info(f"Set daily cost limit for {provider_type.value} to ${limit}")

    def set_provider_priority(self, provider_type: ProviderType, priority: int):
        """Set the priority for a provider (lower = higher priority)."""
        config = self.provider_configs.get(provider_type)
        if config:
            config.priority = priority
            logger.info(f"Set priority for {provider_type.value} to {priority}")

    def reset_daily_stats(self):
        """Reset daily statistics for all providers."""
        with self._lock:
            for health in self.provider_health.values():
                health.total_cost_today = 0.0
                health.requests_today = 0
                health.error_rate_1h = 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers."""
        stats = {
            "providers": {},
            "failover_history": [
                {
                    "timestamp": e.timestamp,
                    "from": e.from_provider.value,
                    "to": e.to_provider.value,
                    "reason": e.reason.value,
                    "error": e.error_message
                }
                for e in self._failover_history[-50:]  # Last 50 events
            ],
            "total_cost_today": 0.0
        }

        for provider_type, provider in self.providers.items():
            health = self.provider_health.get(provider_type)
            config = self.provider_configs.get(provider_type)

            provider_stats = provider.get_stats()
            provider_stats.update({
                "priority": config.priority if config else 0,
                "daily_cost_limit": config.daily_cost_limit if config else 0,
                "enabled": config.enabled if config else False,
                "is_healthy": health.is_healthy if health else False,
                "consecutive_errors": health.consecutive_errors if health else 0,
                "cost_today": health.total_cost_today if health else 0,
                "requests_today": health.requests_today if health else 0,
                "in_cooldown": (
                    health.cooldown_until is not None and
                    datetime.now() < health.cooldown_until
                ) if health else False
            })

            stats["providers"][provider_type.value] = provider_stats
            stats["total_cost_today"] += health.total_cost_today if health else 0

        return stats

    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available providers."""
        return [
            pt for pt in self.providers.keys()
            if self._is_provider_available(pt)
        ]


# Global provider manager instance
_provider_manager: Optional[ProviderManager] = None
_provider_manager_lock = threading.Lock()


def get_provider_manager(
    anthropic_key: Optional[str] = None,
    openai_key: Optional[str] = None,
    **kwargs
) -> ProviderManager:
    """
    Get or create the global provider manager.

    Args:
        anthropic_key: Anthropic API key
        openai_key: OpenAI API key
        **kwargs: Additional configuration options

    Returns:
        Global ProviderManager instance
    """
    global _provider_manager

    with _provider_manager_lock:
        if _provider_manager is None:
            _provider_manager = ProviderManager(
                anthropic_key=anthropic_key,
                openai_key=openai_key,
                **kwargs
            )
        return _provider_manager


def reset_provider_manager():
    """Reset the global provider manager (for testing)."""
    global _provider_manager
    with _provider_manager_lock:
        _provider_manager = None
