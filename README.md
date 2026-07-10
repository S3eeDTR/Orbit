# ORBIT

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Compatible-orange)](https://openrouter.ai/)
[![Version](https://img.shields.io/badge/version-v0.1.0-blue)](https://github.com/S3eeDTR/Orbit/releases)

A terminal-first, project-aware AI coding assistant powered by OpenRouter.

---

> **Warning**
>
> ORBIT is under active development. Commands, internal APIs, and workflows may change before the first stable release.

## Overview

ORBIT is an open-source AI coding assistant inspired by tools such as Claude Code, Codex CLI, Cursor, and Gemini CLI.

It provides a local terminal interface for understanding, searching, editing, and validating software projects using language models available through OpenRouter.

ORBIT is designed around a provider-agnostic architecture. Developers can switch between supported models without changing their workflow or becoming dependent on a single AI provider.

Current capabilities include:

* Project-aware AI conversations
* Streaming model responses
* Persistent conversation history
* Safe workspace operations
* AI-generated file edits
* Transactional multi-file editing
* AI-assisted project planning
* Persistent semantic project indexing
* Read, search, find, and grep tools
* Safe terminal command execution
* Diff previews and user confirmations
* Automatic post-edit validation

The long-term goal is to build a complete terminal-based AI development environment with planning, tools, memory, recovery, and autonomous workflows.

---

## Screenshot

<p align="center">
  <img src="assets/ORBITV1.png" alt="ORBIT Startup" width="900">
</p>

---

# Features

## AI Chat

* OpenRouter integration
* Support for compatible OpenRouter models
* Streaming responses
* Conversation history
* Interactive model switching
* Markdown rendering
* Syntax-highlighted code blocks
* Session statistics
* Saved sessions

## Project Awareness

* Automatic project scanning
* Project file autocomplete
* File references using `@filename`
* AI-generated file descriptions
* Persistent semantic project index
* Incremental indexing using file hashes
* Changed-file detection
* Deleted-file cleanup
* Cached project context for faster planning

## File Editing

* AI-generated full-file replacements
* Unified diff previews
* Explicit confirmation before applying changes
* Single-file editing
* Planner-driven multi-file editing
* Transactional multi-file writes
* Rollback when a multi-file write fails
* Optional file backups

## Workspace Tools

* Read files
* Create files
* Delete files
* Rename files
* Copy files
* Move files
* Append text
* Replace text
* Find files by name or glob
* Search text across the project
* Grep with file paths and line numbers
* Protection against paths outside the project root

## Terminal Tools

* Safe command execution
* `git status`
* `git diff`
* `pytest`
* Custom approved commands
* Command output and exit-code display

## Planning and Validation

* AI-first file planning
* Filename heuristic fallback
* Semantic project descriptions
* Small-file-set selection
* Post-edit syntax validation
* Validation for single-file and multi-file edits

---

# Installation

Clone the repository:

```bash
git clone https://github.com/S3eeDTR/Orbit.git
cd Orbit
```

Install ORBIT in editable mode:

```bash
pip install -e .
```

Launch ORBIT:

```bash
orbit
```

Alternatively:

```bash
python -m orbit
```

---

# Requirements

* Python 3.11 or newer
* OpenRouter API key

Create an OpenRouter API key at:

```text
https://openrouter.ai/keys
```

---

# First Run

The first time ORBIT starts, it will:

1. Request your OpenRouter API key
2. Verify the API key
3. Retrieve available models
4. Ask you to choose a default model
5. Save the local configuration

Configuration is stored under:

```text
~/.config/orbit/
```

Typical configuration files include:

```text
config.json
models.json
history.json
recent.json
sessions/
cache/
logs/
```

Project-specific semantic index data is stored inside the project:

```text
.orbit/project_map.json
```

This file should remain excluded from Git.

---

# Quick Start

Start ORBIT:

```bash
orbit
```

Example prompts:

```text
Explain @orbit/client.py
```

```text
Review @orbit/planner.py and suggest improvements
```

```text
edit orbit/agent.py to improve error handling
```

```text
improve validation across the editing workflow
```

```text
read orbit/project_map.py
```

```text
find files planner
```

```text
search for ProjectMap
```

```text
grep apply_proposals
```

---

# Commands

## Interactive Commands

| Command             | Description                                    |
| ------------------- | ---------------------------------------------- |
| `/help`             | Display available commands                     |
| `/clear`            | Clear conversation history                     |
| `/model`            | Open the interactive model selector            |
| `/model <number>`   | Switch using a displayed model number          |
| `/model <model-id>` | Switch using an OpenRouter model ID            |
| `/models`           | List available models                          |
| `/run <command>`    | Run an approved terminal command               |
| `/index`            | Update the persistent project index            |
| `/index --refresh`  | Rebuild the entire persistent project index    |
| `/index --changed`  | Re-index new and changed files                 |
| `/files`            | Display indexed project files                  |
| `/init`             | Create or load `ORBIT.md` project instructions |
| `/save`             | Save the current chat session                  |
| `/stats`            | Display session statistics                     |
| `/exit`             | Exit ORBIT                                     |

## Shell Commands

These commands are run from the normal operating-system terminal, not from inside the ORBIT prompt:

```bash
orbit
```

```bash
orbit index
```

```bash
orbit index --refresh
```

```bash
orbit index --changed
```

---

# Working With Files

ORBIT can attach local project files to prompts using `@`.

Explain a file:

```text
Explain @main.py
```

Review a module:

```text
Review @orbit/client.py
```

Compare files:

```text
Compare @orbit/client.py with @orbit/chat.py
```

Review multiple files:

```text
Review @orbit/client.py @orbit/models.py @orbit/config.py
```

Referenced files are read from the current project and added to the model context.

Files outside the project root cannot be accessed through the workspace layer.

---

# AI File Editing

ORBIT supports explicit single-file editing.

Examples:

```text
edit orbit/app.py to improve startup error handling
```

```text
fix orbit/chat.py to handle empty API responses
```

```text
refactor orbit/editor.py to reduce duplicated logic
```

```text
optimize orbit/planner.py to avoid unnecessary work
```

The single-file editing workflow is:

```text
User instruction
        ↓
Execution plan
        ↓
User confirmation
        ↓
AI-generated replacement
        ↓
Diff preview
        ↓
User confirmation
        ↓
Apply changes
        ↓
Validation
```

---

# Multi-File Editing

General editing requests can trigger planner-driven multi-file changes.

Example:

```text
improve error handling across the editing workflow
```

ORBIT may select several related files:

```text
orbit/agent.py
orbit/editor.py
orbit/tool_router.py
```

The multi-file workflow is:

```text
User request
        ↓
AI planner
        ↓
Select required files
        ↓
User confirms the plan
        ↓
Generate all file edits
        ↓
Show all diffs
        ↓
User confirms once
        ↓
Apply transactionally
        ↓
Validate
```

If a write fails during the multi-file transaction, ORBIT attempts to restore previously modified files to their original contents.

---

# Read, Search, and Grep Tools

ORBIT provides local project inspection tools that do not require an LLM call.

Read a file:

```text
read orbit/agent.py
```

Find files by name:

```text
find files planner
```

Find files using a glob:

```text
find files *.py
```

Search text across the project:

```text
search for ProjectMap
```

Grep with paths and line numbers:

```text
grep apply_proposals
```

Example output:

```text
orbit/editor.py:112: def apply_proposals(
orbit/agent.py:184: self.editor.apply_proposals(proposals)
```

Generated, dependency, and version-control folders are skipped automatically.

Typical ignored directories include:

```text
.git
.orbit
.venv
venv
node_modules
__pycache__
build
dist
```

---

# Project Indexing

ORBIT maintains two forms of project awareness:

1. A lightweight project file index
2. A persistent semantic project map

The semantic project map is stored at:

```text
.orbit/project_map.json
```

Each indexed entry stores:

```json
{
  "path": "orbit/chat.py",
  "summary": "Handles conversations with the OpenRouter API.",
  "file_hash": "sha256:...",
  "last_modified": 1783648800.0
}
```

The persistent project map allows the planner to reuse cached file descriptions instead of asking the language model to summarize every file during every planning request.

## Index Commands

Create or incrementally update the index:

```bash
orbit index
```

Rebuild all summaries:

```bash
orbit index --refresh
```

Update new and modified files:

```bash
orbit index --changed
```

The interactive equivalents are:

```text
/index
/index --refresh
/index --changed
```

Deleted files are removed from the persistent index during updates.

---

# Post-Edit Validation

ORBIT validates applied edits using a safe terminal command.

The current default validation command is:

```bash
python -m compileall orbit
```

Validation runs after:

* Single-file AI edits
* Multi-file AI edits

The validation result is shown in a terminal panel with:

* Command output
* Exit code
* Success or failure state

Automatic repair retries are planned but are not yet part of the stable editing workflow.

---

# Safe Terminal Execution

ORBIT can run approved terminal commands.

Inside ORBIT:

```text
git status
```

```text
git diff
```

```text
run tests
```

```text
pytest
```

```text
/run python -m compileall orbit
```

Commands are routed through the `Terminal` component, which is responsible for applying execution restrictions.

---

# Model Selection

ORBIT supports models available through OpenRouter.

Open the interactive model selector:

```text
/model
```

Switch using a displayed number:

```text
/model 14
```

Switch using a complete model ID:

```text
/model anthropic/claude-sonnet-4
```

The active model can be changed without restarting ORBIT.

---

# Architecture

```text
                         User
                          │
                          ▼
                    PromptShell
                          │
                          ▼
                     ToolRouter
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
         Workspace     Terminal       Agent
                                       │
                                       ▼
                                    Planner
                                       │
                              Persistent ProjectMap
                                       │
                                       ▼
                                  ChatSession
                                       │
                                       ▼
                               OpenRouterClient
                                       │
                                       ▼
                                    Editor
                                       │
                                       ▼
                                   Workspace
```

## Editing Flow

```text
User request
     │
     ▼
ToolRouter
     │
     ▼
Planner
     │
     ▼
ProjectMap
     │
     ▼
Agent
     │
     ▼
ChatSession
     │
     ▼
Editor
     │
     ▼
Workspace
     │
     ▼
Terminal validation
```

---

# Project Structure

```text
Orbit/
│
├── orbit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent.py
│   ├── app.py
│   ├── banner.py
│   ├── chat.py
│   ├── client.py
│   ├── commands.py
│   ├── config.py
│   ├── constants.py
│   ├── editor.py
│   ├── models.py
│   ├── planner.py
│   ├── project.py
│   ├── project_map.py
│   ├── prompt_shell.py
│   ├── sessions.py
│   ├── terminal.py
│   ├── tool_router.py
│   ├── ui.py
│   └── workspace.py
│
├── assets/
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

---

# Module Overview

| Module            | Responsibility                                               |
| ----------------- | ------------------------------------------------------------ |
| `__main__.py`     | Shell command entry point                                    |
| `agent.py`        | Coordinates planning, editing, confirmation, and validation  |
| `app.py`          | Application lifecycle and dependency initialization          |
| `banner.py`       | Startup and prompt rendering                                 |
| `chat.py`         | Conversation management and AI edit generation               |
| `client.py`       | OpenRouter API communication                                 |
| `commands.py`     | Interactive slash-command handling                           |
| `config.py`       | Configuration loading and persistence                        |
| `constants.py`    | Shared application constants                                 |
| `editor.py`       | Edit proposals, diffs, writes, and transactional application |
| `models.py`       | Model discovery and selection                                |
| `planner.py`      | AI and heuristic file planning                               |
| `project.py`      | Project scanning and lightweight indexing                    |
| `project_map.py`  | Persistent semantic project indexing                         |
| `prompt_shell.py` | Interactive prompt interface                                 |
| `sessions.py`     | Session persistence                                          |
| `terminal.py`     | Safe terminal command execution                              |
| `tool_router.py`  | Natural-language tool routing                                |
| `ui.py`           | Shared terminal UI helpers                                   |
| `workspace.py`    | Safe filesystem and search operations                        |

---

# Design Principles

## Terminal First

ORBIT is designed for developers who prefer working directly inside a terminal.

No graphical interface is required.

## Provider Agnostic

The editing and project workflows are separated from the underlying model provider.

OpenRouter allows developers to use different models while keeping the same ORBIT interface.

## Local Project Control

Filesystem operations, project indexing, diffs, confirmations, and terminal commands are handled locally.

Only content passed into model requests is sent to the selected model provider.

## Explicit Confirmation

Potentially destructive actions require confirmation.

This includes:

* File deletion
* File movement
* AI-generated edits
* Multi-file execution plans
* Applying generated diffs

## Least Privilege

Workspace operations are restricted to the project root.

Terminal execution is routed through a safety layer rather than giving unrestricted shell access directly to the model.

## Recoverability

Multi-file edits preserve original content during the transaction and attempt rollback when a write fails.

Future agent loops will extend recovery to validation failures and failed repair attempts.

## Simplicity

ORBIT avoids unnecessary abstractions.

Each module has a focused responsibility and can evolve independently.

---

# Security and Privacy

ORBIT restricts workspace paths to the active project root.

The workspace layer prevents path traversal outside the project.

Project metadata is stored locally.

Files explicitly referenced or selected for AI processing may be sent to the configured OpenRouter model.

Developers should avoid sending secrets, credentials, private keys, or sensitive production data to external models.

Generated edits should always be reviewed before they are applied.

---

# Development Setup

Clone the repository:

```bash
git clone https://github.com/S3eeDTR/Orbit.git
cd Orbit
```

Install in editable mode:

```bash
pip install -e .
```

Run ORBIT:

```bash
orbit
```

Run a syntax check:

```bash
python -m compileall orbit
```

Run tests:

```bash
pytest
```

Inspect changes:

```bash
git diff
```

---

# Coding Standards

Contributors should follow these guidelines:

* Target Python 3.11+
* Use type hints
* Follow PEP 8
* Keep functions focused
* Keep modules small
* Handle failures explicitly
* Avoid unnecessary dependencies
* Preserve safe project-root boundaries
* Add user confirmation before destructive actions
* Write clear commit messages
* Run syntax checks and tests before committing

---

# Roadmap

## Completed

* OpenRouter AI chat
* Streaming responses
* Conversation history
* Model switching
* Project file indexing
* Safe workspace operations
* Safe terminal execution
* AI-generated file editing
* Diff previews
* AI planning
* Semantic project mapping
* Persistent project index
* Incremental changed-file indexing
* Transactional multi-file editing
* Read, find, search, and grep tools
* Post-edit validation

## In Progress

* Controlled validation-repair loop
* Automatic retries with strict limits
* Better validation command selection
* Recovery after failed generated edits

## Planned

* Agent memory
* Persistent task history
* Project knowledge reuse
* Symbol and export indexing
* Dependency-aware planning
* Background task execution
* Git-aware editing workflows
* Checkpoint and restore support
* Tool calling
* MCP integration
* Plugin system
* Local model support
* Ollama integration
* Multi-agent workflows
* Autonomous coding tasks

---

# Frequently Asked Questions

## Why OpenRouter?

OpenRouter provides access to many language models through one API.

ORBIT provides a consistent coding workflow while allowing developers to choose the model that best fits their task.

## Does ORBIT support local models?

Not yet.

Support for Ollama, LM Studio, and other local providers is planned.

## Is my entire project uploaded automatically?

No.

ORBIT scans and indexes projects locally.

Files selected for AI planning, summarization, or editing may be included in model requests.

## Does ORBIT edit files?

Yes.

ORBIT supports:

* Single-file editing
* Multi-file editing
* Diff previews
* Confirmation before applying
* Transactional batch application
* Post-edit validation

## Can ORBIT run terminal commands?

Yes, through its safe terminal execution layer.

The model does not receive unrestricted shell access.

## Does ORBIT automatically repair failed edits?

Not yet.

Post-edit validation is available. A controlled repair loop with strict retry limits is under development.

## Can I use any OpenRouter model?

ORBIT is designed to work with compatible models exposed through OpenRouter.

Model capabilities may vary, especially for large code-editing tasks.

---

# Contributing

Contributions are welcome.

You can help by:

* Fixing bugs
* Improving documentation
* Adding tests
* Improving platform support
* Proposing new tools
* Strengthening safety controls
* Improving planning and recovery workflows

For significant architectural changes, open an issue first so the design can be discussed.

---

# Versioning

ORBIT follows Semantic Versioning:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
0.1.0
```

* **MAJOR** — Breaking changes
* **MINOR** — New functionality
* **PATCH** — Bug fixes

---

# License

ORBIT is released under the MIT License.

See the `LICENSE` file for details.

---

# Acknowledgements

ORBIT builds on several open-source tools and services:

* Python
* Rich
* prompt_toolkit
* Requests
* OpenRouter

---

# Future Vision

ORBIT aims to become a complete terminal-based AI development environment rather than only an AI chat client.

The long-term direction combines:

* Project understanding
* Persistent memory
* Safe tool execution
* Multi-file editing
* Planning
* Validation
* Recovery
* Autonomous task execution
* Multiple AI model providers

ORBIT will remain lightweight, extensible, provider-agnostic, and terminal-first while giving developers control over how AI interacts with their projects.

---

# Star the Project

If you find ORBIT useful, consider starring the repository.

Feedback, bug reports, feature requests, and contributions help shape the project.
