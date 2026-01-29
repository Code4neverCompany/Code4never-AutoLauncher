# Code4Never AutoLauncher

![AutoLauncher Banner](assets/banner.png)

> **Latest Release: v1.8.4** | [View Changelog](RELEASE_NOTES.md)

A modern, intelligent desktop automation tool designed to schedule, execute, and manage your applications with precision. Built with **PyQt6** and **Fluent Design** for a premium Windows 11 experience.

## ✨ Key Features

### 🚀 Intelligent Task Execution

- **Smart Process Tracking**: Tracks the *actual* application process, even if you launch a shortcut (`.lnk`) or a game launcher (e.g., Riot Client, Plarium Play).
- **Native OCR Detection**: Reads text inside game windows (DirectX/OpenGL) to detect update/maintenance dialogs.
- **Smart Restart**: Automatically restarts stuck applications that display unresponsive dialogs.
- **Double-Click Edit**: Quickly modify any task with a simple double-click.

### 🧩 Addon System (NEW in v1.8.0)

- **Extensible Architecture**: Extend AutoLauncher with community or custom addons.
- **Beacon Sentinel**: Built-in addon that monitors game launchers for update dialogs and auto-dismisses them.
- **Dedicated Addons Page**: Easily enable, disable, and manage your installed extensions.

### 🌙 Advanced Power Management

- **Wake from Sleep**: Automatically wakes your computer to run scheduled tasks.
- **Pre-wake Process**: Wakes the system 1-15 minutes *before* the task starts to ensure everything is ready (network, updates, etc.).
- **Sleep after Completion**: Automatically puts the system back to sleep once the *actual* application closes.

### 🎨 Premium User Experience

- **Fluent Design**: Beautiful, native-feeling UI with Mica effects and acrylic transparency.
- **Theme Support**: Seamlessly switches between Light and Dark modes.
- **Bilingual**: Full support for English and German.
- **Real-time Countdown**: Always know exactly when the next task will run.

## 🛠️ Quick Start

1. **Download**: Get the latest release from the [Releases Page](../../releases).
2. **Install**: Run the installer or extract the portable ZIP.
3. **Run**: Launch `c4n-AutoLauncher.exe`.
4. **Add Task**: Click "Add Task", select your program (exe or shortcut), and set the time.
5. **Relax**: The app will handle the rest, including waking up your PC!

## 🗺️ Roadmap

### ✅ Shipped

- [x] **Plugin/Addon System**: Extensible architecture for community addons (v1.8.0).
- [x] **Native OCR Detection**: Read game UI text for update detection (v1.6.0).
- [x] **MVC Architecture**: Clean separation of UI and logic (v1.7.0).

### 🚧 Planned

- [ ] **Smart Auto-Update**: Intelligently install updates when no tasks are imminent.
- [ ] **Cloud Sync**: Sync tasks across multiple devices.
- [ ] **Advanced Triggers**: Run tasks on startup, network connection, or specific system events.
- [ ] **Task Chaining**: Run Task B automatically after Task A finishes.

## 📜 License

Copyright © 2026 **Code4Never**.
**Non-Commercial Source License**.
Free to use, modify, and distribute. **Selling this software is strictly prohibited.**
See [LICENSE](LICENSE) for details.

---

*Created with ❤️ by Code4Never & Antigravity*
