# Test Strategy - Performance Benchmarking (Milestone 1)

## Overview
Establish baseline performance metrics for the current claude-3-5-haiku-20241022 model used by TDD Coordinator. This testing milestone focuses on measuring and documenting current model performance to enable meaningful comparison after migration to claude-sonnet-4-5-20250929.

## Target Coverage Goals
- **Unit Test Coverage**: 80%+ for benchmarking utilities
- **Integration Test Coverage**: 100% for API endpoints used in benchmarking
- **E2E Coverage**: Critical benchmark execution paths

## Test Categories

---

### 1. Unit Tests

#### Task 1.1: Benchmark Metrics Collection Tests
**Priority**: High
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_metric_collector_captures_response_time` - Verify response time measurement accuracy
2. `test_metric_collector_captures_token_count` - Verify input/output token counting
3. `test_metric_collector_captures_success_failure` - Verify success/failure classification
4. `test_metric_collector_handles_timeout` - Verify timeout scenarios are recorded correctly
5. `test_metric_collector_handles_api_errors` - Verify API error responses are tracked

**Fixtures Needed**:
- Mock API responses (success, failure, timeout)
- Sample prompt/response pairs with known token counts

---

#### Task 1.2: Statistical Analysis Utility Tests
**Priority**: High
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_calculate_success_rate` - Verify success rate calculation from sample data
2. `test_calculate_average_response_time` - Verify mean response time calculation
3. `test_calculate_p95_response_time` - Verify 95th percentile calculation
4. `test_calculate_token_efficiency` - Verify tokens per successful response ratio
5. `test_handle_empty_dataset` - Verify graceful handling of no data
6. `test_handle_all_failures_dataset` - Verify handling of 0% success rate

**Fixtures Needed**:
- Sample benchmark result datasets (small, medium, large)
- Edge case datasets (empty, all failures, all successes)

---

#### Task 1.3: Benchmark Configuration Tests
**Priority**: Medium
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_load_benchmark_config_from_file` - Verify config file parsing
2. `test_validate_benchmark_config_schema` - Verify schema validation
3. `test_default_config_values` - Verify defaults are applied correctly
4. `test_config_override_mechanism` - Verify environment/CLI overrides work

**Fixtures Needed**:
- Sample valid configuration files
- Invalid configuration files for negative testing

---

### 2. Integration Tests

#### Task 2.1: TDD Coordinator Model Response Tests
**Priority**: Critical
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_tdd_coordinator_generates_valid_test_code` - Verify model outputs parseable test code
2. `test_tdd_coordinator_follows_test_format` - Verify output adheres to expected test structure
3. `test_tdd_coordinator_handles_complex_prompts` - Verify handling of multi-file test scenarios
4. `test_tdd_coordinator_rate_limiting` - Verify rate limiting doesn't break functionality
5. `test_tdd_coordinator_retry_on_transient_failure` - Verify retry logic works

**Fixtures Needed**:
- Real test generation prompts (simple, medium, complex)
- Expected response patterns for validation

---

#### Task 2.2: Benchmark Data Persistence Tests
**Priority**: High
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_benchmark_results_saved_to_storage` - Verify results are persisted
2. `test_benchmark_results_retrieval` - Verify results can be loaded for analysis
3. `test_benchmark_results_append_mode` - Verify new results append to existing
4. `test_benchmark_results_isolation_by_model` - Verify results segregated by model version
5. `test_benchmark_results_timestamp_accuracy` - Verify timestamps are correct

**Fixtures Needed**:
- Test database/storage instance
- Sample benchmark result records

---

#### Task 2.3: ActivityTracker Integration for Benchmarks
**Priority**: Medium
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_benchmark_run_recorded_in_activity_tracker` - Verify benchmark runs are tracked
2. `test_benchmark_metrics_appear_in_api_response` - Verify metrics visible via API
3. `test_benchmark_history_queryable` - Verify historical benchmarks retrievable

**Fixtures Needed**:
- Mock ActivityTracker instance
- Sample benchmark execution records

---

### 3. End-to-End Tests

#### Task 3.1: Complete Benchmark Execution Flow
**Priority**: Critical
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_e2e_benchmark_full_execution` - Run complete benchmark suite against haiku model
2. `test_e2e_benchmark_results_report_generation` - Verify report is generated after run
3. `test_e2e_benchmark_comparison_baseline` - Verify baseline can be compared

**Fixtures Needed**:
- Controlled test prompts with expected outputs
- Baseline performance expectations

---

#### Task 3.2: Benchmark CLI/API Interface Tests
**Priority**: Medium
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_benchmark_cli_start_command` - Verify benchmark can be triggered via CLI
2. `test_benchmark_api_endpoint` - Verify benchmark can be triggered via API
3. `test_benchmark_progress_reporting` - Verify progress is visible during execution
4. `test_benchmark_cancellation` - Verify benchmark can be safely cancelled

**Fixtures Needed**:
- CLI test harness
- API test client

---

### 4. Performance/Load Tests

#### Task 4.1: Benchmark Stress Tests
**Priority**: Low (for Milestone 1)
**Assigned To**: TDD Coordinator

**Test Cases**:
1. `test_benchmark_handles_rapid_requests` - Verify no data loss under load
2. `test_benchmark_metric_accuracy_under_load` - Verify metrics remain accurate
3. `test_benchmark_memory_stability` - Verify no memory leaks during long runs

**Fixtures Needed**:
- Load testing framework configuration
- Resource monitoring hooks

---

## Test Implementation Order

### Phase 1: Foundation (Critical Path)
1. Task 1.1 - Benchmark Metrics Collection Tests
2. Task 1.2 - Statistical Analysis Utility Tests
3. Task 2.1 - TDD Coordinator Model Response Tests

### Phase 2: Integration
4. Task 2.2 - Benchmark Data Persistence Tests
5. Task 1.3 - Benchmark Configuration Tests
6. Task 2.3 - ActivityTracker Integration for Benchmarks

### Phase 3: End-to-End Validation
7. Task 3.1 - Complete Benchmark Execution Flow
8. Task 3.2 - Benchmark CLI/API Interface Tests

### Phase 4: Hardening (Optional for M1)
9. Task 4.1 - Benchmark Stress Tests

---

## Mocking Strategy

### External Dependencies to Mock
1. **Anthropic API Calls** - Mock for unit tests, use real API for integration/E2E
2. **File System Operations** - Mock for unit tests
3. **ActivityTracker** - Mock for isolated unit tests, real for integration
4. **Time/Clock** - Mock for deterministic timing tests

### Mock Implementation Guidelines
```python
# Example mock patterns for TDD Coordinator

# Mock Anthropic API response
@pytest.fixture
def mock_haiku_response():
    return {
        "content": [{"text": "def test_example():\n    assert True"}],
        "usage": {"input_tokens": 150, "output_tokens": 50},
        "stop_reason": "end_turn"
    }

# Mock timing decorator
@pytest.fixture
def mock_timer():
    return MagicMock(elapsed_ms=lambda: 250.0)
```

---

## Test Data Requirements

### Baseline Benchmark Dataset
1. **Simple Test Generation Prompts** (10 samples)
   - Single function tests
   - Basic assertions
   
2. **Medium Complexity Prompts** (10 samples)
   - Multi-function tests
   - Mock requirements
   
3. **Complex Prompts** (5 samples)
   - Integration test scenarios
   - Multiple file dependencies

### Expected Metrics to Capture
| Metric | Description | Target Baseline |
|--------|-------------|-----------------|
| Success Rate | % of prompts generating valid tests | Current: TBD |
| Response Time (avg) | Mean time to generate response | Current: TBD |
| Response Time (p95) | 95th percentile response time | Current: TBD |
| Token Efficiency | Output tokens per successful response | Current: TBD |
| Error Rate | % of API errors/timeouts | Current: TBD |

---

## Acceptance Criteria

### Milestone 1 Complete When:
- [ ] All Phase 1 tests passing
- [ ] All Phase 2 tests passing
- [ ] At least one successful E2E benchmark run completed
- [ ] Baseline metrics documented for haiku model
- [ ] Test coverage >= 80% for new benchmark code
- [ ] Results stored in format compatible with comparison (Milestone 2)

### Quality Gates:
- All unit tests pass in < 30 seconds
- Integration tests pass in < 2 minutes
- E2E benchmark completes in < 10 minutes
- No flaky tests (100% pass rate on 3 consecutive runs)

---

## Handoff Notes for TDD Coordinator

1. **Start with Task 1.1** - Metrics collection is the foundation
2. **Use pytest** - Standard pytest with pytest-asyncio for async tests
3. **Mock external APIs** - Don't make real API calls in unit tests
4. **Capture real baselines** - E2E tests should capture actual haiku performance
5. **Document results** - Store baseline metrics in a structured format for M2 comparison

---

*Test Strategy Author: Test Coordinator Agent*
*Created: 2026-01-14*
*Milestone: Performance Benchmarking - Baseline Metrics (M1)*
