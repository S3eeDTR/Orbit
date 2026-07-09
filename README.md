# ORBIT

A terminal-first AI coding assistant powered by OpenRouter.

ORBIT is an open-source developer CLI inspired by modern AI coding tools such as Claude Code and Gemini CLI. It provides a fast, interactive command-line experience for working with hundreds of large language models through a single interface.

The long-term vision is to build an extensible AI development environment capable of understanding projects, managing context, editing code, executing tools, and supporting complex software engineering workflows.

---

## Features

Current capabilities include:

- Interactive terminal interface
- Support for any OpenRouter model
- Switch models without restarting the session
- Conversation history
- Rich terminal rendering
- Markdown and syntax-highlighted output
- Local configuration management
- Session statistics
- Project-aware workflow
- File reference support (`@file.py`)

---

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/orbit.git
cd orbit
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install ORBIT locally:

```bash
pip install -e .
```

Run:

```bash
orbit
```

---

## First Run

The first launch will:

1. Request your OpenRouter API key
2. Download the latest available models
3. Allow you to choose a default model
4. Store your configuration locally

Configuration is stored in:

```
~/.config/openrouter-cli/
```

---

## Commands

| Command | Description |
|----------|-------------|
| `/help` | Show available commands |
| `/models` | List available models |
| `/model <id>` | Switch to another model |
| `/clear` | Clear the conversation |
| `/stats` | Display session statistics |
| `/exit` | Exit ORBIT |

---

## Working with Files

Reference files directly in your prompt.

```text
Explain @main.py

Review @database.py

Refactor @api.py
```

Multiple files may be referenced.

```text
Compare @old.py with @new.py
```

---

## Model Selection

Switch models using either the displayed number

```text
/model 15
```

or the complete model identifier

```text
/model anthropic/claude-opus-4.1
```

---

## Project Structure

```
orbit/
│
├── openrouter_cli/
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
│   ├── prompt_shell.py
│   ├── project.py
│   ├── sessions.py
│   └── ui.py
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Roadmap

### Near Term

- Streaming responses
- Better markdown rendering
- Interactive model picker
- Project indexing
- Better file context handling

### Mid Term

- Git integration
- File editing
- Shell tool execution
- Workspace memory
- Conversation export

### Long Term

- Multi-agent workflows
- Tool calling
- Plugin system
- MCP support
- Autonomous coding tasks
- Cross-platform installer

---

## Why ORBIT?

Most AI coding assistants are tightly coupled to a single provider.

ORBIT takes a different approach by separating the interface from the model. Through OpenRouter, developers can seamlessly switch between models from OpenAI, Anthropic, Google, Meta, Qwen, DeepSeek, Mistral, and many others without changing tools or workflows.

The goal is to provide a consistent, provider-agnostic development experience while allowing users to choose the model that best fits their task.

---

## Contributing

Contributions are welcome.

If you plan to implement a significant feature or architectural change, please open an issue first so it can be discussed before development begins.

Bug reports, documentation improvements, and pull requests are all appreciated.

---

## License

This project is licensed under the MIT License.
