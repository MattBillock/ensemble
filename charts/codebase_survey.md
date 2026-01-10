# Agent System Architecture Survey

## Runtime Structure
The agent system has a core runtime implementation centered in `src/runtime/agents/` with three main components:

### 1. Agent Definition (`definition.py`)
- Responsible for parsing and loading agent type definitions from markdown files
- Key class: `AgentDefinition`
- Parses markdown files to extract:
  - Name
  - Purpose
  - Instantiation conditions
  - Termination conditions
  - Input/Output formats
  - Instructions
  - Metadata like model preferences

### 2. Agent Runtime (`runtime.py`)
- Manages agent execution using Anthropic API
- Key class: `AgentRuntime`
- Features:
  - Model selection (Haiku, Sonnet, Opus)
  - Input validation
  - Iteration management
  - Tool integration
  - Response parsing
  - Logging and error handling

### 3. Tools Management (`tools.py`)
- Not detailed in this survey, but referenced for tool registry and execution

## Key Architectural Components

### Input Processing
- Agent definitions specify detailed input formats
- Runtime validates inputs against specified schema
- JSON-based communication model

### Execution Model
- Supports multiple iterations (configurable max_iterations)
- Tool use support
- Dynamic system and user prompt generation
- Built-in clarification and termination condition handling

### Model Interaction
- Uses Anthropic Claude models
- Model selection through friendly names (haiku, sonnet, opus)
- Supports tool calling and advanced prompt engineering

## Technologies
- Language: Python
- API: Anthropic Claude
- Logging: Structured JSON logging
- Parsing: Regular expressions for markdown parsing
- Type Hints: Extensive type annotations

## Notable Design Patterns
- Factory method for agent definition creation
- Flexible configuration through markdown
- Separation of definition, runtime, and tool concerns