# c4n-AutoLauncher - Roadmap & Future Plans

> **Current Version**: v1.8.4 | [View Changelog](RELEASE_NOTES.md)

---

## ✅ Recently Shipped

### v1.8.5 - Smart Auto-Update *(In Development)*

- **Task-Aware Updates**: Defers updates when scheduled tasks are imminent (<30 min)
- **Zero Interruption**: Queues updates until after task completion
- **Automatic Trigger**: Proceeds with update after all imminent tasks finish

### v1.8.0 - Addon System

- **Plugin Architecture**: Extensible system for community addons
- **Beacon Sentinel Addon**: Monitors game launchers for update dialogs
- **Dedicated Addons UI**: Enable/disable addons from the sidebar

### v1.7.0 - MVC Architecture

- **Clean Separation**: UI (View) decoupled from Logic (Controller)
- **Atomic Writes**: Safe save mechanism prevents data corruption
- **Zombie Process Cleanup**: Background collector for orphaned processes

### v1.6.0 - Native OCR Detection

- **Windows OCR**: Reads text inside DirectX/OpenGL game windows
- **Smart Restart**: Auto-restarts stuck applications with unresponsive dialogs

---

## 🚧 Planned Features

### Priority 1: Core Improvements

#### Codebase Modularization 🏗️

**Status**: Technical Debt | **Effort**: 4+ hours

Break down monolithic files for maintainability:

- `scheduler.py` (50KB) → Split into core, hooks, UI bridge
- `settings_interface.py` (50KB) → Extract setting groups
- `autolauncher.py` (60KB) → Separate UI components

---

### Priority 2: Feature Enhancements

#### Task Execution Analytics 📊

- Track task success/failure history
- Show execution patterns and trends
- Identify frequently failing tasks

#### Beacon Sentinel UI Enhancement 🔍

- Always-visible indicator in toolbar (grayed when inactive, cyan when active)
- Settings toggle to enable/disable entirely
- Configurable monitoring duration

#### Advanced Scheduling ⏰

- Conditional triggers ("run when specific program closes")
- Day-of-week specific schedules
- Holiday/vacation mode to pause all tasks

---

### Priority 3: Future Vision

#### Task Chaining 🔗

- Run Task B automatically after Task A finishes
- Define dependencies between tasks

#### Performance Monitoring 📈

- Show resource usage of launched programs
- Alert if programs consume excessive resources
- Auto-kill programs exceeding thresholds

---

## Contributing

Have ideas for features? Open an issue on [GitHub](https://github.com/Code4neverCompany/Code4never-AutoLauncher/issues) with the `enhancement` label!

---

© 2026 4never Company. All rights reserved.
