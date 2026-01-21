# v1.8.2 (2026-01-21) - Hotfix: Settings Crash
This critical hotfix resolves a startup crash caused by an incorrect widget configuration in the Settings menu.

### Fixes
*   **CRITICAL FIX**: Resolved `AttributeError: 'int' object has no attribute 'range'` when initializing the "Idle Threshold" setting.
*   **Stability**: Implemented a compatibility layer for `RangeSettingCard` to ensure safe operation.
