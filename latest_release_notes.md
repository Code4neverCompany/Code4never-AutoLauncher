# v1.8.3 (2026-01-23) - Hotfix: Import Error
This critical hotfix resolves a startup crash caused by a missing import in the Settings module.

### Fixes
*   **CRITICAL FIX**: Resolved `NameError: name 'QObject' is not defined` when initializing ManualRangeConfigItem.
