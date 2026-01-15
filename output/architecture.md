# Fix Output Directory Structure - Architecture

## System Overview
This project involves migrating existing output files from a nested source directory to the project root output directory and updating agent configurations to use the new location.

## Architecture Components

### 1. File System Migration
**Current State**:
- Output files located at: `/src/field/ensemble_ui/output/`
- Approximately 100+ files including requirements, architecture docs, milestone plans
- Existing directory structure and file organization

**Target State**:
- Output files at: `/Users/mattbillock/Development/ai_exploration/ensemble/output/`
- Same file organization and naming conventions
- Root-level accessibility for users

### 2. Agent Configuration System
**Components to Update**:
- Agent prompt templates with hardcoded output paths
- Configuration files referencing old directory
- Path resolution logic in agent spawning
- Documentation and references

**Configuration Files**:
- Agent prompt files (*.md templates)
- System configuration files
- Documentation files with path references

### 3. Git Integration
**Migration Strategy**:
- Use `git mv` commands to preserve history
- Batch operations for efficiency
- Verify integrity after migration

## Technical Approach

### Phase 1: Directory Setup
1. Create new output directory structure
2. Set proper permissions and accessibility
3. Verify directory creation

### Phase 2: File Migration
1. Identify all files in current output directory
2. Use git mv to preserve history during migration
3. Maintain existing directory structure within new location
4. Verify all files transferred successfully

### Phase 3: Configuration Updates
1. Scan for hardcoded paths in agent configurations
2. Update prompt templates with new output directory
3. Modify any configuration files
4. Update internal documentation

### Phase 4: Validation
1. Test agent output generation to new location
2. Verify file accessibility and permissions
3. Confirm no broken references
4. Clean up old directory

## Data Flow
1. **Current**: Agent → `/src/field/ensemble_ui/output/` → Files stored in nested location
2. **Target**: Agent → `/Users/mattbillock/Development/ai_exploration/ensemble/output/` → Files stored at root level

## Dependencies
- Git repository for version control
- File system permissions for directory creation/modification
- Agent configuration system access

## Risk Mitigation
- Use git mv to preserve file history
- Backup verification before old directory removal
- Incremental validation throughout migration
- Test agent functionality before finalization

## Success Criteria
- All files successfully migrated to new location
- Agent configurations updated and functional
- No broken references or missing files
- User can access outputs easily at root level