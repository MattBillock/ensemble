# Milestone 0: Foundation Fixes - Requirements Document

## Project Overview
Clean up technical debt, consolidate redundant agents, implement cost controls, and apply initial Domain-Driven Design principles to create a solid foundation for future UI development.

## Core Objectives

### 1. Terminology Cleanup
- Remove all drum corps references across project files
- Standardize agent documentation language

### 2. Agent Consolidation
- Reduce total number of agents from 23 to 14
- Merge redundant agent roles while maintaining functionality
- Update AGENT_REGISTRY.md with new agent structure

### 3. Executive Director Coordination Fix
- Add validation for requirements file before spawning Development Manager
- Ensure robust agent spawning process

### 4. Budget Tier System Implementation
- Create tiered model selection system
- Add budget_tier parameter to agent spawning
- Implement cost control mechanisms

### 5. Domain-Driven Design Refactoring
- Create domain layer structure
- Extract core domain entities
- Implement repository interface
- Maintain existing functionality

### 6. CI/CD Setup
- Install pre-commit hooks
- Create GitHub Actions workflow
- Enable local and remote automated testing

## Success Criteria
- 0 drum corps references in active agent files
- 14 total agents (down from 23)
- Working budget tier selection
- Fully functional domain layer
- Comprehensive test coverage
- Working pre-commit and CI/CD configuration

## Constraints
- Maintain backward compatibility
- No breaking changes to existing system
- Preserve current test coverage
- Ensure consolidated agents retain original functionality

## Out of Scope
- UI implementation
- Event bus implementation
- LLM provider abstraction
- Performance metrics collection
- Always-on task monitoring

## Deliverables
1. Updated agent definition files
2. New Python modules for model selection and domain layer
3. CI/CD configuration files
4. Updated documentation
5. Comprehensive test suite

## Testing Requirements
- Unit tests for new modules
- Integration tests for agent consolidation
- Coverage target: 80%+ overall, 90%+ for domain layer