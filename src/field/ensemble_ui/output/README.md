# Output Directory

This directory consolidates all output artifacts from the ensemble project in one centralized location.

## Directory Structure

```
output/
├── README.md           # This file
├── requirements.md     # Project requirements documentation
├── projects/           # Generated code projects and applications
├── tests/              # Test results, coverage reports, and test artifacts
├── logs/               # Execution logs and traces
├── reports/            # Generated reports and analysis
├── docs/               # Generated documentation
└── temp/               # Temporary files and scratch space
```

## Directory Descriptions

### `projects/`
Contains complete generated code projects, applications, and implementations created by the ensemble agents.
- Organized by project name or timestamp
- Each subdirectory should be a self-contained project

### `tests/`
Test execution results, coverage reports, and test-related artifacts.
- Unit test results
- Integration test results
- Test coverage reports
- Performance test results

### `logs/`
Execution logs, traces, and debugging information.
- Agent execution logs
- Error logs
- Debug traces
- Performance metrics

### `reports/`
Generated reports and analysis documents.
- Status reports
- Performance analysis
- Code quality reports
- Project summaries

### `docs/`
Generated documentation artifacts.
- API documentation
- Architecture diagrams
- User guides
- Technical specifications

### `temp/`
Temporary files and scratch space.
- Work-in-progress files
- Intermediate build artifacts
- Cache files
- Files safe to delete

## Usage Guidelines

### For Agents
- Write all output to the appropriate subdirectory
- Use descriptive filenames with timestamps when needed
- Clean up temporary files when no longer needed
- Document significant outputs in project notes

### For Users
- Browse projects/ for completed implementations
- Check tests/ for test results and quality metrics
- Review logs/ for execution details and debugging
- Read reports/ for project summaries and status

## Naming Conventions

- **Projects**: `{project_name}/` or `{project_name}_{timestamp}/`
- **Test Results**: `test_results_{project_name}_{timestamp}.json`
- **Logs**: `{agent_type}_{timestamp}.log`
- **Reports**: `{report_type}_{project_name}_{date}.md`

## Version Control

Most output files are excluded from version control via `.gitignore`:
- Temporary files are never tracked
- Logs are excluded
- Generated code projects may be tracked selectively
- Documentation and reports may be tracked for history

## Maintenance

- Temporary files can be cleaned up periodically
- Old logs can be archived or removed
- Test results may be retained for historical comparison
- Projects should be reviewed before deletion
