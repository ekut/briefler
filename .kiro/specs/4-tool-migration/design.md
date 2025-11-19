# Design Document: Tool Migration

## Overview

This design describes the migration of the GmailReaderTool from `src/mailbox_briefler/tools/` to `src/briefler/tools/`. The migration consolidates the codebase by moving the tool implementation into the main application package, eliminating the separate `mailbox_briefler` package while maintaining full functionality and updating all references.

### Key Objectives

- Move GmailReaderTool file to the main briefler package
- Update all import statements across the codebase
- Clean up the old package structure
- Update documentation and configuration files
- Verify functionality is preserved

## Architecture

### Current Structure

```
src/
├── briefler/
│   ├── __init__.py
│   ├── main.py
│   ├── crews/
│   │   └── gmail_reader_crew/
│   │       └── gmail_reader_crew.py  (imports from mailbox_briefler)
│   ├── flows/
│   └── tools/
│       ├── __init__.py
│       └── custom_tool.py  (legacy/template)
└── mailbox_briefler/
    └── tools/
        ├── __init__.py
        └── gmail_reader_tool.py  (to be moved)
```

### Target Structure

```
src/
└── briefler/
    ├── __init__.py
    ├── main.py
    ├── crews/
    │   └── gmail_reader_crew/
    │       └── gmail_reader_crew.py  (imports from briefler.tools)
    ├── flows/
    └── tools/
        ├── __init__.py
        └── gmail_reader_tool.py  (moved here)
```

## Components and Interfaces

### 1. File Migration

**Source File:** `src/mailbox_briefler/tools/gmail_reader_tool.py`
**Target File:** `src/briefler/tools/gmail_reader_tool.py`

**Actions:**
- Copy the file to the new location
- Verify file integrity (no changes to content)
- Delete the original file after verification

**No Code Changes Required:**
The GmailReaderTool implementation does not need any internal modifications. All imports within the file (google-auth, crewai, etc.) are external dependencies and remain valid.

### 2. Package Initialization Updates

**File:** `src/briefler/tools/__init__.py`

**Current State:**
```python
from briefler.tools.custom_tool import CustomTool

__all__ = ['CustomTool']
```

**Target State:**
```python
from briefler.tools.gmail_reader_tool import GmailReaderTool

__all__ = ['GmailReaderTool']
```

**Changes:**
- Import GmailReaderTool instead of CustomTool
- Export GmailReaderTool in `__all__` list
- Remove CustomTool if it's not used elsewhere

### 3. Import Statement Updates

#### 3.1 Crew File

**File:** `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`

**Current Import:**
```python
from mailbox_briefler.tools.gmail_reader_tool import GmailReaderTool
```

**Target Import:**
```python
from briefler.tools.gmail_reader_tool import GmailReaderTool
```

#### 3.2 Example File

**File:** `examples/gmail_reader_example.py`

**Current Import:**
```python
from mailbox_briefler.tools.gmail_reader_tool import GmailReaderTool
```

**Target Import:**
```python
from briefler.tools.gmail_reader_tool import GmailReaderTool
```

### 4. Documentation Updates

#### 4.1 Structure Steering File

**File:** `.kiro/steering/structure.md`

**Current Content:**
```markdown
`src/mailbox_briefler/tools/` - Gmail API tool implementation
```

**Target Content:**
```markdown
`src/briefler/tools/` - Gmail API tool implementation (GmailReaderTool)
```

**Additional Changes:**
- Update the tools section description to clarify that `src/briefler/tools/` now contains the Gmail tool
- Remove any references to legacy/template tools if custom_tool.py is removed

#### 4.2 Spec Files

**Files to Update:**
- `.kiro/specs/gmail-reader-tool/design.md` - Update component structure section
- `.kiro/specs/gmail-reader-tool/tasks.md` - Update file paths in task descriptions
- `.kiro/specs/enhanced-crew-input-parameters/design.md` - Update GmailReaderTool location reference
- `.kiro/specs/crewai-structure-conversion/design.md` - Update import statement examples
- `.kiro/specs/crewai-structure-conversion/requirements.md` - Update import path requirement

**Pattern:**
Replace all occurrences of:
- `src/mailbox_briefler/tools/` → `src/briefler/tools/`
- `mailbox_briefler.tools.gmail_reader_tool` → `briefler.tools.gmail_reader_tool`
- `from mailbox_briefler.tools` → `from briefler.tools`

### 5. Cleanup Operations

#### 5.1 Remove Old Package

**Directory to Remove:** `src/mailbox_briefler/`

**Verification Before Removal:**
1. Confirm no other files reference `mailbox_briefler` package
2. Confirm GmailReaderTool is successfully imported from new location
3. Run a test import to verify functionality

**Steps:**
1. Delete `src/mailbox_briefler/tools/gmail_reader_tool.py`
2. Delete `src/mailbox_briefler/tools/__init__.py`
3. Delete `src/mailbox_briefler/tools/` directory
4. Delete `src/mailbox_briefler/` directory

#### 5.2 Remove Legacy Tool (Optional)

**File:** `src/briefler/tools/custom_tool.py`

**Condition:** Remove if not used elsewhere in the codebase

**Verification:**
- Search for imports of `custom_tool` or `CustomTool`
- If no references found, delete the file
- Update `__init__.py` accordingly

## Data Models

No data model changes are required. The GmailReaderTool maintains its existing:
- Input schema: `GmailReaderToolInput` (Pydantic model)
- Output format: Formatted string with message data
- Internal data structures: Message dictionaries, attachment metadata

## Error Handling

### Migration Errors

**Import Errors:**
- **Cause:** Stale Python bytecode cache (`.pyc` files)
- **Solution:** Clear `__pycache__` directories after migration
- **Prevention:** Delete old package completely before testing

**Module Not Found Errors:**
- **Cause:** Missed import statement updates
- **Solution:** Search entire codebase for `mailbox_briefler` references
- **Prevention:** Use comprehensive grep search before declaring migration complete

**Circular Import Errors:**
- **Cause:** Unlikely, but possible if package initialization is incorrect
- **Solution:** Verify `__init__.py` files are properly structured
- **Prevention:** Follow Python package best practices

### Verification Strategy

1. **Static Analysis:**
   - Search for all occurrences of `mailbox_briefler` in codebase
   - Verify no references remain after updates

2. **Import Testing:**
   - Test import: `from briefler.tools.gmail_reader_tool import GmailReaderTool`
   - Verify tool instantiation: `tool = GmailReaderTool()`

3. **Functional Testing:**
   - Run example script: `python examples/gmail_reader_example.py`
   - Run crew: `crewai run` or `python src/briefler/main.py`

## Testing Strategy

### Pre-Migration Verification

1. **Baseline Test:**
   - Run the application with current structure
   - Verify GmailReaderTool works correctly
   - Document current behavior

### Post-Migration Verification

1. **Import Tests:**
   - Test new import path works
   - Test old import path fails (as expected)
   - Verify no import errors in application startup

2. **Functional Tests:**
   - Run example scripts
   - Execute crew with GmailReaderTool
   - Verify OAuth flow still works
   - Verify message retrieval functionality

3. **Integration Tests:**
   - Run full application flow
   - Test with actual Gmail credentials (if available)
   - Verify no regressions in functionality

### Test Checklist

- [ ] New import path works: `from briefler.tools.gmail_reader_tool import GmailReaderTool`
- [ ] Tool instantiation succeeds: `tool = GmailReaderTool()`
- [ ] Example script runs: `python examples/gmail_reader_example.py`
- [ ] Crew example runs: `python examples/gmail_crew_example.py`
- [ ] Main application runs: `python src/briefler/main.py`
- [ ] No references to `mailbox_briefler` remain in codebase
- [ ] Old package directory is removed
- [ ] Documentation is updated

## Migration Sequence

### Phase 1: Preparation
1. Verify current functionality works
2. Identify all files that import from `mailbox_briefler`
3. Create backup of current state (via git)

### Phase 2: File Migration
1. Copy `gmail_reader_tool.py` to `src/briefler/tools/`
2. Update `src/briefler/tools/__init__.py`
3. Verify file integrity

### Phase 3: Import Updates
1. Update crew file imports
2. Update example file imports
3. Search for any other references

### Phase 4: Documentation Updates
1. Update steering files
2. Update spec files
3. Update any README or documentation

### Phase 5: Cleanup
1. Remove old `mailbox_briefler` package
2. Remove legacy `custom_tool.py` if unused
3. Clear Python cache directories

### Phase 6: Verification
1. Test new import path
2. Run example scripts
3. Run full application
4. Verify no errors

## Rollback Plan

If issues are encountered during migration:

1. **Immediate Rollback:**
   - Revert all file changes via git
   - Restore original package structure

2. **Partial Rollback:**
   - Keep both packages temporarily
   - Add compatibility imports in `__init__.py`:
     ```python
     # Backward compatibility
     from briefler.tools.gmail_reader_tool import GmailReaderTool
     ```

3. **Gradual Migration:**
   - Keep old package as deprecated
   - Add deprecation warnings
   - Migrate imports gradually

## Performance Considerations

**No Performance Impact Expected:**
- File location does not affect runtime performance
- Import paths are resolved at module load time
- No changes to tool logic or algorithms

**Potential Benefits:**
- Simplified package structure may slightly reduce import resolution time
- Cleaner codebase improves maintainability

## Security Considerations

**No Security Impact:**
- No changes to authentication logic
- No changes to credential handling
- No changes to API access patterns

**Verification:**
- Ensure `.env` file paths remain valid
- Verify OAuth flow still works correctly
- Confirm token storage location unchanged

## Future Enhancements

After successful migration:

1. **Tool Organization:**
   - Consider adding more tools to `src/briefler/tools/`
   - Organize tools by category if needed

2. **Package Structure:**
   - Evaluate if other packages need consolidation
   - Standardize package naming conventions

3. **Documentation:**
   - Update architecture diagrams
   - Create migration guide for future reference
