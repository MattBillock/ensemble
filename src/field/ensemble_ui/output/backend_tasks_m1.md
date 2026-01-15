# Backend Tasks - Runtime Token Extraction and Basic Integration

## Task Breakdown

### 1. Token Extraction Core Implementation
- **Name**: Implement TokenUsage Data Class
- **Description**: Create robust token tracking data structure
- **Location**: `src/runtime/agents/runtime.py`
- **Acceptance Criteria**:
  - Correctly captures input_tokens, output_tokens
  - Provides total_tokens calculation
  - Supports token accumulation across iterations
- **Complexity**: Simple
- **Dependencies**: None

### 2. Activity Tracker Token Enhancement
- **Name**: Modify Activity Tracker to Store Token Data
- **Description**: Update activity tracking to include token usage information
- **Location**: `src/runtime/agents/activity_tracker.py`
- **Acceptance Criteria**:
  - Can store token data alongside existing agent state
  - Maintains backward compatibility
  - Provides token data retrieval methods
- **Complexity**: Medium
- **Dependencies**: 
  - Task 1: TokenUsage Data Class

### 3. Runtime Token Extraction from Anthropic Responses
- **Name**: Develop Token Extraction Mechanism
- **Description**: Implement reliable token extraction from Anthropic API responses
- **Location**: `src/runtime/agents/runtime.py`
- **Acceptance Criteria**:
  - Successfully extracts tokens from mock and real API responses
  - Handles cases where token data might be missing
  - Provides default/fallback token values
- **Complexity**: Medium
- **Dependencies**: 
  - Task 1: TokenUsage Data Class
  - Task 2: Activity Tracker Token Enhancement

### 4. API Endpoint Token Data Integration
- **Name**: Enhance API Responses with Token Usage
- **Description**: Modify existing API endpoints to include token data
- **Location**: `src/field/ensemble_ui/backend/main.py`
- **Acceptance Criteria**:
  - `/api/agents/state` includes token usage data
  - `/api/requests/{request_id}/timeline` shows token information
  - No breaking changes to existing API contract
- **Complexity**: Medium
- **Dependencies**:
  - Task 1: TokenUsage Data Class
  - Task 2: Activity Tracker Token Enhancement
  - Task 3: Runtime Token Extraction

### 5. Token Extraction Error Handling and Logging
- **Name**: Implement Robust Error Handling for Token Extraction
- **Description**: Create defensive mechanisms for token data collection
- **Location**: `src/runtime/agents/runtime.py`
- **Acceptance Criteria**:
  - Gracefully handles missing token data
  - Logs warnings for token extraction failures
  - Does not interrupt agent execution
- **Complexity**: Simple
- **Dependencies**:
  - Task 3: Runtime Token Extraction

## Testing Tasks

### 6. Unit Tests for Token Extraction
- **Name**: Develop Comprehensive Unit Tests
- **Description**: Create unit tests for token extraction and tracking
- **Location**: `tests/runtime/test_token_extraction.py`
- **Acceptance Criteria**:
  - 100% coverage of TokenUsage data class
  - Verify token accumulation logic
  - Test edge cases with missing/incomplete token data
- **Complexity**: Medium
- **Dependencies**:
  - Task 1: TokenUsage Data Class
  - Task 3: Runtime Token Extraction

### 7. Integration Tests for Token Flow
- **Name**: Create End-to-End Token Tracking Tests
- **Description**: Verify token data flows correctly through system
- **Location**: `tests/integration/test_token_tracking.py`
- **Acceptance Criteria**:
  - Token data correctly stored in activity tracker
  - API endpoints return token information
  - No performance degradation
- **Complexity**: Complex
- **Dependencies**:
  - Task 2: Activity Tracker Token Enhancement
  - Task 4: API Endpoint Token Data Integration
  - Task 6: Unit Tests for Token Extraction

## Task Dependencies Graph
```
1. TokenUsage Data Class
│
├─→ 2. Activity Tracker Token Enhancement
│   │
│   └─→ 4. API Endpoint Token Data Integration
│
├─→ 3. Runtime Token Extraction
│   │
│   ├─→ 5. Token Extraction Error Handling
│   │
│   └─→ 6. Unit Tests for Token Extraction
│       │
│       └─→ 7. Integration Tests for Token Flow
```

## Estimated Timeline
- **Week 1**: Tasks 1-3 (Core Token Extraction)
- **Week 2**: Tasks 4-7 (Integration and Testing)

## Performance and Quality Gates
- All tasks must maintain <1ms latency impact
- 100% unit test coverage
- Zero breaking changes to existing system