# Implementation Plan

- [x] 1. Verify current state and prepare for migration
  - Check that GmailReaderTool currently works by attempting to import it
  - Search codebase for all references to `mailbox_briefler` to identify files that need updates
  - _Requirements: 1.2, 5.1_

- [ ] 2. Migrate the GmailReaderTool file
  - [x] 2.1 Copy gmail_reader_tool.py to target location
    - Copy file from `src/mailbox_briefler/tools/gmail_reader_tool.py` to `src/briefler/tools/gmail_reader_tool.py`
    - Verify file content is identical after copy
    - _Requirements: 1.1, 1.2_
  
  - [x] 2.2 Update src/briefler/tools/__init__.py
    - Import GmailReaderTool from `briefler.tools.gmail_reader_tool`
    - Add GmailReaderTool to `__all__` list
    - Remove CustomTool import and export if custom_tool.py is not used
    - _Requirements: 1.4, 3.1_

- [ ] 3. Update import statements in application code
  - [x] 3.1 Update crew file import
    - Modify `src/briefler/crews/gmail_reader_crew/gmail_reader_crew.py`
    - Change import from `mailbox_briefler.tools.gmail_reader_tool` to `briefler.tools.gmail_reader_tool`
    - _Requirements: 2.1, 2.4_
  
  - [x] 3.2 Update example file import
    - Modify `examples/gmail_reader_example.py`
    - Change import from `mailbox_briefler.tools.gmail_reader_tool` to `briefler.tools.gmail_reader_tool`
    - _Requirements: 2.2, 2.4_

- [ ] 4. Update documentation and configuration files
  - [x] 4.1 Update structure steering file
    - Modify `.kiro/steering/structure.md`
    - Change reference from `src/mailbox_briefler/tools/` to `src/briefler/tools/`
    - Update description to clarify tools package contents
    - _Requirements: 4.1, 4.5_
  
  - [x] 4.2 Update spec documentation files
    - Update `.kiro/specs/gmail-reader-tool/design.md` with new component structure path
    - Update `.kiro/specs/gmail-reader-tool/tasks.md` with new file paths
    - Update `.kiro/specs/enhanced-crew-input-parameters/design.md` with new GmailReaderTool location
    - Update `.kiro/specs/crewai-structure-conversion/design.md` with new import statement
    - Update `.kiro/specs/crewai-structure-conversion/requirements.md` with new import path
    - _Requirements: 4.2, 4.5_

- [ ] 5. Clean up old package structure
  - [x] 5.1 Remove mailbox_briefler package
    - Delete `src/mailbox_briefler/tools/gmail_reader_tool.py`
    - Delete `src/mailbox_briefler/tools/__init__.py`
    - Delete `src/mailbox_briefler/tools/` directory
    - Delete `src/mailbox_briefler/` directory
    - _Requirements: 1.5, 3.3, 3.4_
  
  - [x] 5.2 Remove legacy custom_tool.py if unused
    - Search codebase for references to `custom_tool` or `CustomTool`
    - If no references found, delete `src/briefler/tools/custom_tool.py`
    - _Requirements: 3.1, 3.2_

- [ ] 6. Verify migration success
  - [x] 6.1 Test new import path
    - Verify Python can import GmailReaderTool from `briefler.tools.gmail_reader_tool`
    - Verify tool instantiation works without errors
    - _Requirements: 5.1, 5.3_
  
  - [x] 6.2 Verify no old references remain
    - Search entire codebase for any remaining references to `mailbox_briefler`
    - Confirm old import path no longer works (as expected)
    - _Requirements: 2.4, 2.5, 5.5_
  
  - [x] 6.3 Test application functionality
    - Run example script to verify it executes without errors
    - Verify GmailReaderTool maintains all functionality
    - _Requirements: 4.4, 5.2, 5.4_
