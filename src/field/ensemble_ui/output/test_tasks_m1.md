# Test Strategy - LocalClaudeProvider CLI Interactions and Circuit Breaker

## Overview
This document defines the comprehensive testing strategy for the LocalClaudeProvider implementation, focusing on CLI interactions, circuit breaker functionality, and integration with the existing model router system.

## Test Coverage Goals
- **Unit Test Coverage**: 85% for LocalClaudeProvider and circuit breaker logic
- **Integration Coverage**: 100% of CLI interaction scenarios and fallback paths
- **E2E Coverage**: Critical user journeys with local provider enabled/disabled

## 1. Unit Tests

### 1.1 LocalClaudeProvider Core Functionality
**File**: `tests/test_local_claude_provider.py`

#### Task LCP-UT-001: CLI Availability Tests
- Test `is_available()` with CLI installed/not installed
- Test `is_available()` with CLI executable/non-executable
- Test `is_available()` with invalid CLI path
- Mock filesystem operations for consistent testing

#### Task LCP-UT-002: CLI Command Construction Tests
- Test basic command format construction
- Test command with system prompt
- Test command with different model selections
- Test command with special characters in prompts
- Test argument escaping and sanitization

#### Task LCP-UT-003: CLI Execution Tests (Mocked)
- Mock subprocess.run for successful CLI execution
- Test timeout handling with hanging processes
- Test CLI exit codes (0, 1, 2, etc.)
- Test stdout/stderr capture and parsing
- Test subprocess exceptions (FileNotFoundError, PermissionError)

#### Task LCP-UT-004: JSON Response Parsing Tests
- Test valid CLI JSON response parsing
- Test malformed JSON handling
- Test missing required fields (result, usage, cost)
- Test unexpected JSON structure
- Test empty/null responses
- Test token count extraction
- Test cost calculation parsing

#### Task LCP-UT-005: Long Prompt Handling Tests
- Test temp file creation for large prompts
- Test temp file cleanup on success/failure
- Test file permission errors
- Test disk space errors
- Mock filesystem operations for edge cases

#### Task LCP-UT-006: LocalExecutionResult Tests
- Test result object creation with all fields
- Test result object with missing optional fields
- Test result serialization/deserialization
- Test error state representation

### 1.2 LocalCircuitBreaker Tests
**File**: `tests/test_local_circuit_breaker.py`

#### Task LCB-UT-001: Circuit Breaker State Management
- Test initial CLOSED state
- Test transition from CLOSED to OPEN after failure threshold
- Test transition from OPEN to HALF_OPEN after cooldown
- Test transition from HALF_OPEN to CLOSED on success
- Test transition from HALF_OPEN to OPEN on failure

#### Task LCB-UT-002: Failure Tracking
- Test consecutive failure counting
- Test failure counter reset on success
- Test failure timestamp recording
- Test cooldown period calculation

#### Task LCB-UT-003: Circuit Breaker Configuration
- Test custom failure threshold values
- Test custom cooldown period values
- Test edge cases (threshold=0, cooldown=0)
- Test invalid configuration handling

#### Task LCB-UT-004: Thread Safety Tests
- Test concurrent access to circuit breaker state
- Test race conditions in state transitions
- Test atomic operations for failure counting

## 2. Integration Tests

### 2.1 ModelRouter Integration
**File**: `tests/test_model_router_local_integration.py`

#### Task MR-INT-001: Local Provider Integration
- Test ModelRouter initialization with LocalClaudeProvider
- Test `should_use_local()` decision logic
- Test provider health check integration
- Test configuration parameter passing

#### Task MR-INT-002: Execution Routing Tests
- Test routing to local provider when healthy
- Test routing to API when local unhealthy
- Test fallback behavior on local execution failure
- Test provider preference configuration

#### Task MR-INT-003: Response Format Compatibility
- Test LocalExecutionResult to API response format conversion
- Test token usage tracking compatibility
- Test cost tracking compatibility
- Test error handling format consistency

### 2.2 Runtime Integration
**File**: `tests/test_runtime_local_integration.py`

#### Task RT-INT-001: AgentRuntime Local Execution
- Test runtime with local provider enabled
- Test runtime with local provider disabled
- Test execution flow with local-first preference
- Test activity tracking with provider information

#### Task RT-INT-002: Fallback Scenarios
- Test automatic fallback on CLI not found
- Test automatic fallback on CLI timeout
- Test automatic fallback on circuit breaker open
- Test metrics recording for fallback scenarios

#### Task RT-INT-003: Configuration Management
- Test environment variable configuration
- Test runtime configuration parameters
- Test configuration validation
- Test invalid configuration handling

## 3. End-to-End Tests

### 3.1 CLI Integration Tests (Real CLI Required)
**File**: `tests/test_e2e_cli_integration.py`
**Note**: Marked with `@pytest.mark.skipif(not cli_available)`

#### Task E2E-CLI-001: Actual CLI Execution
- Test real CLI command execution
- Test actual JSON response parsing
- Test real timeout scenarios
- Test real error conditions (invalid model, etc.)

#### Task E2E-CLI-002: Complete Execution Flow
- Test end-to-end prompt execution via CLI
- Test system prompt integration
- Test model selection
- Test token and cost reporting accuracy

### 3.2 Circuit Breaker E2E Tests
**File**: `tests/test_e2e_circuit_breaker.py`

#### Task E2E-CB-001: Circuit Breaker Lifecycle
- Test circuit breaker opening under real failure conditions
- Test automatic recovery after cooldown
- Test fallback to API during circuit breaker open state
- Test metrics and logging during circuit breaker events

#### Task E2E-CB-002: Load and Stress Testing
- Test circuit breaker under rapid successive failures
- Test behavior under concurrent execution attempts
- Test recovery under load conditions

## 4. Error Scenario Tests

### 4.1 CLI Error Handling
**File**: `tests/test_cli_error_scenarios.py`

#### Task ERR-001: CLI Installation Issues
- Test behavior when CLI not installed
- Test behavior when CLI path invalid
- Test behavior when CLI permissions denied
- Test appropriate error messages and logging

#### Task ERR-002: CLI Execution Failures
- Test CLI subprocess timeout scenarios
- Test CLI crash/segfault scenarios
- Test CLI invalid argument scenarios
- Test CLI output format changes

#### Task ERR-003: System Resource Issues
- Test behavior when disk space full (temp files)
- Test behavior when memory limited
- Test behavior when file descriptor limits reached

### 4.2 Network and Fallback Testing
**File**: `tests/test_fallback_scenarios.py`

#### Task FALL-001: API Fallback Testing
- Test seamless fallback to Anthropic API
- Test response format consistency during fallback
- Test token usage tracking during fallback
- Test activity logging for fallback events

#### Task FALL-002: Provider Availability Testing
- Test behavior when both local and API unavailable
- Test behavior when local recovers after API fallback
- Test provider preference restoration

## 5. Performance Tests

### 5.1 CLI Performance
**File**: `tests/test_cli_performance.py`

#### Task PERF-001: Execution Speed Tests
- Benchmark CLI execution times vs API calls
- Test prompt size impact on execution time
- Test concurrent execution performance
- Test memory usage during execution

#### Task PERF-002: Circuit Breaker Overhead
- Benchmark circuit breaker decision overhead
- Test performance impact of health checking
- Test scaling behavior with high request volume

## 6. Configuration and Environment Tests

### 6.1 Configuration Validation
**File**: `tests/test_configuration.py`

#### Task CONF-001: Environment Variable Tests
- Test all environment variable configurations
- Test configuration precedence (env vs code)
- Test invalid configuration handling
- Test configuration changes at runtime

#### Task CONF-002: Cross-Platform Tests
- Test CLI path resolution on different platforms
- Test subprocess behavior differences
- Test file system permission handling

## 7. Logging and Monitoring Tests

### 7.1 Activity Tracking
**File**: `tests/test_activity_tracking.py`

#### Task LOG-001: Provider Tracking Tests
- Test activity logging with provider information
- Test metrics collection for local vs API usage
- Test cost tracking accuracy
- Test error logging and debugging information

#### Task LOG-002: Debug Information Tests
- Test detailed logging for troubleshooting
- Test log level configuration
- Test sensitive information redaction

## 8. Test Implementation Requirements

### 8.1 Test Infrastructure
- **Mock Strategy**: Use `unittest.mock` for subprocess and filesystem operations
- **CLI Detection**: Implement `cli_available()` fixture for conditional testing
- **Test Data**: Create comprehensive JSON response fixtures
- **Performance Baseline**: Establish timing benchmarks for comparison

### 8.2 Test Coverage Tools
- **Coverage Target**: 85% overall, 95% for critical paths
- **Coverage Tools**: pytest-cov for measurement
- **CI Integration**: All tests must pass in GitHub Actions
- **Documentation**: Each test file must include purpose and scope docstrings

### 8.3 Test Organization
- **Naming Convention**: test_[component]_[scenario]_[expected_outcome]
- **Grouping**: Use pytest marks for test categories (unit, integration, e2e)
- **Fixtures**: Shared fixtures in conftest.py for provider mocking
- **Parameterization**: Use pytest.mark.parametrize for multiple scenarios

## 9. Risk Areas and Edge Cases

### 9.1 High-Risk Scenarios
1. **CLI Version Changes**: Output format compatibility
2. **Concurrent Access**: Thread safety in circuit breaker
3. **Resource Exhaustion**: File descriptor/memory limits
4. **Platform Differences**: CLI behavior across macOS/Linux/Windows

### 9.2 Edge Cases to Test
1. **Extremely Large Prompts**: Beyond system argument limits
2. **Special Characters**: Unicode, control characters, shell metacharacters
3. **Rapid State Changes**: Circuit breaker state race conditions
4. **Clock Adjustments**: System time changes affecting cooldown

## 10. Success Metrics

### 10.1 Test Completion Criteria
- All 45+ test tasks implemented and passing
- 85%+ code coverage achieved
- Performance benchmarks established
- E2E tests passing with actual CLI
- CI/CD pipeline integration complete

### 10.2 Quality Gates
- Zero critical security vulnerabilities
- All error paths covered with tests
- Comprehensive logging verification
- Cross-platform compatibility confirmed
- Documentation for all test scenarios

This comprehensive test strategy ensures robust validation of the LocalClaudeProvider implementation while maintaining the high reliability standards expected for production deployment.