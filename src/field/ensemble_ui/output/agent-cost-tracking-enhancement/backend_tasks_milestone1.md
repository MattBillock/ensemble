# Backend Tasks - Milestone 1: Backend Tracking Infrastructure

## Task 1: Implement CostCalculator Module
- **Description**: Create `cost_calculator.py` to calculate token-based cost estimates
- **Acceptance Criteria**:
  - Supports cost calculation for Claude models (Opus, Sonnet, Haiku)
  - Handles input and output token pricing
  - Provides fallback estimation method
- **Dependencies**: None
- **Complexity**: Medium

## Task 2: Extend ActivityTracker Data Structures
- **Description**: Update activity_tracker.py to capture new agent execution metrics
- **Acceptance Criteria**:
  - Add fields for `started_at`, `completed_at`, `duration_ms`
  - Add fields for `model_used`, `cost_estimate`
  - Add `token_usage` sub-structure
  - Ensure backward compatibility
- **Dependencies**: Task 1 (CostCalculator)
- **Complexity**: Medium

## Task 3: Modify AgentRuntime for Metric Tracking
- **Description**: Update AgentRuntime to capture and calculate execution metrics
- **Acceptance Criteria**:
  - Record start time on initialization
  - Extract token usage from Claude API responses
  - Calculate execution duration
  - Use CostCalculator to estimate execution cost
  - Pass metrics to activity tracker
- **Dependencies**: Task 1, Task 2
- **Complexity**: Complex

## Task 4: Update API Endpoint Responses
- **Description**: Modify API responses to include new agent execution metrics
- **Acceptance Criteria**:
  - Add new fields to agent state responses
  - Ensure new fields are optional (backward compatibility)
  - Format timestamps in ISO format
  - Include duration, cost estimate, and model information
- **Dependencies**: Task 2, Task 3
- **Complexity**: Simple

## Task 5: Implement Unit Tests for New Components
- **Description**: Create comprehensive unit tests for new and modified components
- **Acceptance Criteria**:
  - Test CostCalculator with various models and token scenarios
  - Test ActivityTracker data structure updates
  - Test AgentRuntime metric calculation
  - Test API response formatting
  - Achieve > 90% code coverage
- **Dependencies**: Task 1, Task 2, Task 3, Task 4
- **Complexity**: Complex

## Task 6: Performance and Error Handling Validation
- **Description**: Validate performance impact and error handling for new metrics tracking
- **Acceptance Criteria**:
  - Verify metric calculation overhead is < 5ms
  - Handle scenarios with missing token usage
  - Gracefully manage unknown models
  - No performance degradation in agent execution
- **Dependencies**: All previous tasks
- **Complexity**: Complex

## Task 7: Documentation and Code Comments
- **Description**: Update documentation for new components and changes
- **Acceptance Criteria**:
  - Document CostCalculator usage and pricing model
  - Comment complex logic in ActivityTracker
  - Update README/architecture docs
  - Include examples of new metric tracking
- **Dependencies**: All previous tasks
- **Complexity**: Simple