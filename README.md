# ORBIT

**A modern terminal-first AI coding assistant powered by OpenRouter.**

ORBIT is an open-source AI developer CLI inspired by modern coding assistants such as Claude Code and Gemini CLI. It provides a fast, interactive terminal interface for working with hundreds of large language models through OpenRouter while maintaining a consistent developer experience.

The goal of ORBIT is to become a provider-agnostic AI development environment capable of understanding projects, editing code, executing tools, managing long-running conversations, and assisting throughout the complete software development lifecycle.

> **Project Status:** Early Development (v0.1.0)

---

## Features

### Current

- Interactive terminal interface
- Support for all OpenRouter models
- Switch models without restarting
- Conversation history
- Rich terminal rendering
- Markdown rendering
- Syntax highlighted code blocks
- Local configuration management
- Session statistics
- Project-aware workflow
- File references (`@filename.py`)

### Planned

- Streaming responses
- Project indexing
- Automatic context retrieval
- File editing
- Git integration
- Tool execution
- Workspace memory
- Multi-agent workflows
- Model Context Protocol (MCP)
- Plugin architecture

---

# Installation

Clone the repository

```bash
git clone https://github.com/S3eeDTR/Orbit.git
cd Orbit
```

Install the dependencies

```bash
pip install -r requirements.txt
```

Install ORBIT

```bash
pip install -e .
```

Run

```bash
orbit
```

---

# First Run

The first time ORBIT starts it will automatically:

- Request your OpenRouter API key
- Download the available model list
- Let you choose a default model
- Save your configuration locally

Configuration is stored under:

```
~/.config/openrouter-cli/
```

---

# Commands

| Command | Description |
|----------|-------------|
| `/help` | Show available commands |
| `/models` | List available models |
| `/model <id>` | Switch models |
| `/clear` | Clear the current conversation |
| `/stats` | Show session statistics |
| `/exit` | Exit ORBIT |

---

# Working With Files

Reference project files directly inside your prompts.

```text
Explain @main.py
```

```text
Review @database.py
```

```text
Refactor @client.py
```

Multiple files can also be referenced.

```text
Compare @api.py with @api_old.py
```

---

# Model Selection

Models can be selected using either their displayed number

```text
/model 12
```

or their complete identifier

```text
/model anthropic/claude-opus-4.1
```

---

# Project Structure

```
Orbit/
│
├── orbit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py
│   ├── banner.py
│   ├── chat.py
│   ├── client.py
│   ├── commands.py
│   ├── config.py
│   ├── constants.py
│   ├── file_context.py
│   ├── models.py
│   ├── project.py
│   ├── prompt_shell.py
│   ├── sessions.py
│   └── ui.py
│
├── tests/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
└── .gitignore
```

---

# Architecture

```
                    Terminal
                       │
                       ▼
             Interactive Prompt
                       │
                       ▼
              Command Dispatcher
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
  Conversation Engine          Project Context
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
               OpenRouter Client
                       │
                       ▼
              OpenRouter REST API
```

---

# Roadmap

## Version 0.2

- Streaming responses
- Better markdown rendering
- Interactive model picker
- Project indexing
- Better file context

---

## Version 0.3

- Git integration
- File editing
- Shell tool execution
- Workspace memory
- Conversation export

---

## Version 0.4

- Multi-agent workflows
- Autonomous coding tasks
- Code review agent
- Documentation generation
- Test generation

---

## Version 1.0

- Complete AI development environment
- Plugin system
- MCP support
- Long-term memory
- Cross-platform installer
- Native package distribution

---

# Technology Stack

- Python 3.11+
- OpenRouter API
- Rich
- prompt_toolkit
- Requests

---

# Why ORBIT?

Most AI coding assistants are tightly coupled to a single provider.

ORBIT separates the developer experience from the underlying model, allowing users to switch seamlessly between OpenAI, Anthropic, Google, Meta, Qwen, DeepSeek, Mistral, and many other providers available through OpenRouter without changing workflows.

The long-term vision is to build a flexible AI platform where developers choose the best model for each task while keeping a consistent interface and workflow.

---

# Contributing

Contributions are welcome.

If you plan to implement a significant feature or architectural change, please open an issue first to discuss the proposal before starting development.

Bug reports, documentation improvements, feature requests, and pull requests are all appreciated.

---

# Disclaimer

ORBIT is an independent open-source project and is not affiliated with, endorsed by, or sponsored by OpenRouter or any model provider.

---

# License

This project is licensed under the MIT License.

See the LICENSE file for details.
