# Architecture: Ensemble Output Organization System

## System Overview
A file organization and tracking system that automatically categorizes, organizes, and indexes all agent-generated output files into a project-based structure with dynamic change tracking.

---

## Architecture Principles
1. **Single Source of Truth**: One centralized output directory for all agent artifacts
2. **Convention Over Configuration**: Automatic categorization based on file naming patterns
3. **Non-Breaking**: Backward compatible with existing workflows
4. **Low Overhead**: Lightweight operations that don't impact agent performance
5. **Fail-Safe**: Fallback mechanisms for uncategorizable files

---

## System Components

### 1. Directory Structure Manager
**Purpose**: Defines and maintains the hierarchical folder structure

**Responsibilities**:
- Define standard project/category folder structure
- Create directories on-demand when new projects start
- Maintain archive folder for completed projects

**Structure Template**:
```
output/
├── _INDEX.md                    # Dynamic index
├── _ARCHIVE/                    # Completed projects
│   └── {project_name}/
├── {active_project}/
│   ├── requirements/
│   ├── architecture/
│   ├── milestones/
│   ├── tasks/
│   ├── reports/
│   ├── planning/
│   ├── guides/
│   └── status/
└── _uncategorized/              # Fallback
```

### 2. File Categorizer
**Purpose**: Determines the correct category for any given file

**Responsibilities**:
- Analyze filename and optionally content
- Match against categorization rules
- Return category path or fallback to `_uncategorized/`

**Categorization Rules**:
| Pattern | Category |
|---------|----------|
| `*requirements*.md` | requirements/ |
| `*architecture*.md` | architecture/ |
| `*milestone*.md` | milestones/ |
| `*_tasks*.md`, `*backend*.md`, `*frontend*.md` | tasks/ |
| `*report*.md`, `*analysis*.md`, `*audit*.md` | reports/ |
| `*plan*.md`, `*feasibility*.md` | planning/ |
| `*guide*.md`, `*dictionary*.md`, `*reference*.md` | guides/ |
| `*status*.md` | status/ |

**Algorithm**:
```python
def categorize_file(filename: str, project_name: str) -> Path:
    # Pattern matching logic
    for pattern, category in CATEGORY_RULES:
        if pattern_matches(filename, pattern):
            return output_root / project_name / category / filename
    
    # Fallback
    return output_root / project_name / "_uncategorized" / filename
```

### 3. Index Generator
**Purpose**: Creates and maintains `_INDEX.md` with file inventory and recent changes

**Responsibilities**:
- Scan entire output directory tree
- Track file modification times
- Generate Markdown index with:
  - Recent changes (last 20 files)
  - Project groupings
  - Quick links to all files

**Index Structure**:
```markdown
# Ensemble Output Index

**Last Updated**: [timestamp]

## Recent Changes (Last 20)
- [timestamp] [project/category/file.md](link)
...

## Projects
### Project Name
- Requirements: [link]
- Architecture: [link]
- Milestones: [link]
...
```

**Trigger**: Regenerate on every file write operation

### 4. Migration Engine
**Purpose**: One-time migration of existing files to new structure

**Responsibilities**:
- Analyze all existing files in output root
- Determine project association (from filename, content, or metadata)
- Categorize each file
- Move files to correct locations
- Generate migration report

**Migration Process**:
1. **Discovery**: Scan output directory for all `.md` files
2. **Analysis**: Parse filenames, detect project context
3. **Dry Run**: Generate proposed moves without executing
4. **Review**: Present migration plan for approval
5. **Execute**: Move files to new locations
6. **Report**: Document all moves and any issues

**Project Detection Logic**:
- Check for project name in filename (e.g., `logs_agents_tab_requirements.md`)
- Group related files (architecture + milestones + tasks = same project)
- Timestamp-based grouping (files created within same time window)
- Manual mapping for ambiguous cases

### 5. Tool Integration Layer
**Purpose**: Integrate with `WriteFileTool` to enforce structure

**Responsibilities**:
- Intercept file write operations
- Validate output paths
- Suggest correct paths when agents write to wrong locations
- Auto-correct paths (with logging)
- Trigger index regeneration

**Integration Points**:
- Modify `WriteFileTool._run()` method in `/src/runtime/agents/tools.py`
- Add path validation before write
- Add index regeneration after write

**Behavior**:
```python
class WriteFileTool:
    def _run(self, file_path: str, content: str, ...) -> str:
        # NEW: Path validation
        if is_output_path(file_path):
            validated_path = validate_and_suggest_path(
                file_path, 
                current_project_context
            )
            if validated_path != file_path:
                log_warning(f"Path corrected: {file_path} -> {validated_path}")
                file_path = validated_path
        
        # Existing write logic
        result = write_file(file_path, content)
        
        # NEW: Index regeneration
        if is_output_path(file_path):
            regenerate_index()
        
        return result
```

---

## Data Flow

### New File Creation Flow
```
Agent Requests Write
    ↓
WriteFileTool._run()
    ↓
Path Validation
    ↓
[Is Output Path?] → No → Normal Write
    ↓ Yes
File Categorizer
    ↓
Determine Project + Category
    ↓
Construct Correct Path
    ↓
[Path Correct?] → Yes → Write File
    ↓ No
Log Warning + Auto-Correct
    ↓
Write File
    ↓
Index Generator
    ↓
Regenerate _INDEX.md
    ↓
Complete
```

### Migration Flow
```
Run Migration Script
    ↓
Scan Output Directory
    ↓
For Each File:
    ↓
    Detect Project Name
    ↓
    Categorize File
    ↓
    Generate New Path
    ↓
[Dry Run?] → Yes → Add to Report
    ↓ No
Move File
    ↓
Update Migration Report
    ↓
Complete Migration
    ↓
Regenerate Index
```

---

## Module Structure

```
src/runtime/agents/tools/
├── output_organization/
│   ├── __init__.py
│   ├── categorizer.py          # File categorization logic
│   ├── index_generator.py      # Index generation
│   ├── migrator.py              # Migration engine
│   ├── path_validator.py       # Path validation for WriteFileTool
│   └── config.py                # Category rules, paths
├── tools.py (MODIFIED)          # WriteFileTool integration
└── ...

scripts/
└── migrate_output_files.py      # One-time migration script
```

---

## Configuration

### Category Rules Configuration (`config.py`)
```python
CATEGORY_RULES = [
    (r".*requirements.*\.md$", "requirements"),
    (r".*architecture.*\.md$", "architecture"),
    (r".*milestone.*\.md$", "milestones"),
    (r".*tasks.*\.md$", "tasks"),
    (r".*backend.*\.md$", "tasks"),
    (r".*frontend.*\.md$", "tasks"),
    (r".*test.*\.md$", "tasks"),
    (r".*report.*\.md$", "reports"),
    (r".*analysis.*\.md$", "reports"),
    (r".*plan.*\.md$", "planning"),
    (r".*guide.*\.md$", "guides"),
    (r".*status.*\.md$", "status"),
]

OUTPUT_ROOT = Path("/Users/mattbillock/Development/ai_exploration/ensemble/src/field/ensemble_ui/output")

STANDARD_CATEGORIES = [
    "requirements",
    "architecture", 
    "milestones",
    "tasks",
    "reports",
    "planning",
    "guides",
    "status",
]
```

---

## API Design

### Core APIs

#### Categorizer
```python
def categorize_file(filename: str) -> str:
    """Returns category name or '_uncategorized'"""

def get_project_path(project_name: str, category: str, filename: str) -> Path:
    """Constructs full output path"""
```

#### Index Generator
```python
def generate_index() -> None:
    """Scans output directory and creates _INDEX.md"""

def get_recent_changes(limit: int = 20) -> List[FileChange]:
    """Returns list of recent file changes"""
```

#### Path Validator
```python
def validate_output_path(file_path: str, project_context: str) -> str:
    """Validates and corrects output paths"""

def is_output_path(file_path: str) -> bool:
    """Checks if path is in output directory"""
```

#### Migrator
```python
def analyze_files() -> Dict[str, ProjectInfo]:
    """Analyzes existing files and groups by project"""

def migrate_files(dry_run: bool = True) -> MigrationReport:
    """Executes migration with optional dry run"""
```

---

## Error Handling

### Strategy
1. **Graceful Degradation**: If categorization fails, use `_uncategorized/`
2. **Logging**: Log all path corrections and warnings
3. **Backward Compatibility**: Accept old paths with warnings
4. **Validation**: Validate paths before writes, not after

### Error Scenarios
| Scenario | Handling |
|----------|----------|
| Cannot determine category | Place in `_uncategorized/` |
| Project name missing | Use "default_project" |
| Index generation fails | Log error, continue (non-blocking) |
| Migration collision | Append timestamp to filename |
| Invalid path characters | Sanitize and log warning |

---

## Performance Considerations

### Index Regeneration
- **Trigger**: On every write to output directory
- **Cost**: File system scan (~100-500 files)
- **Optimization**: 
  - Only scan output directory (not entire codebase)
  - Cache directory structure
  - Async operation (non-blocking)
- **Estimated Time**: < 100ms for typical project size

### Migration
- **One-time operation**: Not performance-critical
- **Safety**: Use dry-run mode first
- **Backup**: Recommend git commit before migration

---

## Security & Safety

### File Operations
- Validate all paths to prevent directory traversal
- Use Path library for safe path manipulation
- Never delete files, only move them
- Create backups before migration

### Permissions
- Respect file system permissions
- Log permission errors clearly
- Fall back gracefully on permission issues

---

## Testing Strategy

### Unit Tests
- Test categorization rules with various filenames
- Test path validation logic
- Test index generation with mock file system
- Test migration logic with sample data

### Integration Tests
- Test WriteFileTool integration end-to-end
- Test actual file writes trigger index regeneration
- Test migration with real output directory (on copy)

### Test Cases
1. Categorize standard filenames correctly
2. Handle ambiguous filenames (fallback to uncategorized)
3. Validate correct output paths (no change)
4. Correct incorrect output paths (with logging)
5. Generate index with proper structure
6. Migrate files without data loss
7. Handle concurrent writes safely

---

## Deployment Plan

### Phase 1: Foundation (Milestone 1)
- Create module structure
- Implement categorizer and path validator
- Unit tests for core logic

### Phase 2: Migration (Milestone 2)
- Implement migration engine
- Implement index generator
- Dry-run migration
- Execute actual migration
- Generate initial index

### Phase 3: Integration (Milestone 3)
- Modify WriteFileTool
- Test with actual agent operations
- Monitor for issues
- Adjust categorization rules as needed

### Phase 4: Documentation (Milestone 4)
- Write usage guides
- Document category rules
- Create reference documentation
- Final validation

---

## Monitoring & Maintenance

### Metrics to Track
- Files placed in `_uncategorized/` (should be minimal)
- Path corrections made by validator
- Index generation time
- Migration success rate

### Maintenance Tasks
- Review uncategorized files monthly
- Update category rules as needed
- Archive completed projects
- Prune old files from archive

---

## Future Enhancements (Out of Current Scope)
1. Real-time file watching daemon
2. Web-based index viewer with search
3. Automatic project detection from git branch
4. Category suggestions based on file content (ML)
5. Integration with version control for change tracking
6. Multi-language support (non-Markdown files)

---

## Summary

This architecture provides:
✅ Centralized, organized output structure
✅ Automatic categorization with fallback
✅ Dynamic index for easy navigation
✅ Safe migration of existing files
✅ Non-breaking integration with existing tools
✅ Low performance overhead
✅ Clear path forward for implementation

**Key Design Decisions**:
1. **Pattern-based categorization**: Simple, predictable, maintainable
2. **Integration at tool level**: Enforcement without agent modification
3. **Markdown index**: Human-readable, no dependencies
4. **Graceful fallback**: System continues even with ambiguous files
5. **Dry-run migration**: Safety first approach

The system is designed to be lightweight, maintainable, and immediately useful while leaving room for future enhancements.
