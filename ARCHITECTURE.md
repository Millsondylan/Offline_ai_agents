# AI Agent Architecture

## Provider Connection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Dashboard     │  │     CLI      │  │   TUI         │ │
│  │   (Textual)     │  │   Commands   │  │   Interface   │ │
│  └────────┬────────┘  └──────┬───────┘  └───────┬───────┘ │
└───────────┼────────────────────┼───────────────────┼─────────┘
            │                    │                   │
            └────────────────────┼───────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Controller                         │
│              (RealAgentManager / AgentLoop)                 │
│                                                             │
│  1. Monitor repository                                      │
│  2. Run analysis (ruff, pytest, bandit, etc.)              │
│  3. Compose prompt from context                            │
│  4. Request AI model to generate patch                     │
│  5. Apply and verify patch                                 │
│  6. Commit if gates pass                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ provider.generate_patch(prompt)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Provider System (providers/)                   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  provider_from_config()                               │ │
│  │  Routes based on config.provider.type                 │ │
│  └────┬──────────────────────────────────────────────────┘ │
│       │                                                     │
│       ├─► OllamaProvider ─────────────────────────────────┐│
│       │   • HTTP API mode (preferred)                     ││
│       │   • CLI fallback mode                             ││
│       │   • Local model execution                         ││
│       │                                                    ││
│       ├─► HostedAPIProvider ──────────────────────────────┤│
│       │   ├─ OpenAI Backend                               ││
│       │   ├─ Anthropic Backend                            ││
│       │   └─ Gemini Backend                               ││
│       │                                                    ││
│       ├─► CommandProvider ────────────────────────────────┤│
│       │   • Custom shell commands                         ││
│       │                                                    ││
│       └─► ManualProvider ─────────────────────────────────┘│
│           • Manual patch input                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/CLI calls
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Model Backends                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   Ollama     │  │   OpenAI     │  │   Anthropic      │ │
│  │   (Local)    │  │   (Cloud)    │  │   (Cloud)        │ │
│  │              │  │              │  │                  │ │
│  │  deepseek-   │  │  GPT-4       │  │  Claude 3.5      │ │
│  │  coder       │  │  GPT-4o-mini │  │  Sonnet          │ │
│  │  llama3      │  │              │  │  Claude Opus     │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
│                                                             │
│  ┌──────────────┐                                          │
│  │   Gemini     │                                          │
│  │   (Cloud)    │                                          │
│  │              │                                          │
│  │  Gemini 2.0  │                                          │
│  │  Flash       │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. User adds task or agent auto-detects work
   ↓
2. Agent runs analyzers (ruff, pytest, bandit, etc.)
   ↓
3. Agent composes prompt with:
   - Git status
   - Test results
   - Linter output
   - User task
   - Repository context
   ↓
4. Provider sends prompt to AI model
   ┌─────────────────────────────────────┐
   │ Ollama (Local)                      │
   │ • HTTP: POST /api/generate          │
   │ • CLI: ollama run <model>           │
   └─────────────────────────────────────┘
   ┌─────────────────────────────────────┐
   │ OpenAI (Cloud)                      │
   │ POST /v1/chat/completions           │
   └─────────────────────────────────────┘
   ┌─────────────────────────────────────┐
   │ Anthropic (Cloud)                   │
   │ POST /v1/messages                   │
   └─────────────────────────────────────┘
   ┌─────────────────────────────────────┐
   │ Gemini (Cloud)                      │
   │ POST /v1/models/<model>:generate    │
   └─────────────────────────────────────┘
   ↓
5. AI model generates unified diff patch
   ↓
6. Agent applies patch with git apply
   ↓
7. Agent runs production gates:
   - Ruff (linting)
   - Pytest (tests + coverage)
   - Bandit (security)
   - Semgrep (patterns)
   - Pip-audit (dependencies)
   ↓
8. If gates pass → commit to branch
   ↓
9. Optional: push to remote
   ↓
10. Cooldown → repeat
```

## Configuration Examples

### Ollama (Local)
```json
{
  "provider": {
    "type": "ollama",
    "model": "deepseek-coder:6.7b-instruct",
    "base_url": "http://localhost:11434",
    "use_api": true,
    "timeout": 1200
  }
}
```

### OpenAI (Cloud)
```json
{
  "provider": {
    "type": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "timeout": 120
  }
}
```
*Requires: `OPENAI_API_KEY` environment variable*

### Anthropic (Cloud)
```json
{
  "provider": {
    "type": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.2,
    "timeout": 120,
    "max_tokens": 8000
  }
}
```
*Requires: `ANTHROPIC_API_KEY` environment variable*

### Gemini (Cloud)
```json
{
  "provider": {
    "type": "gemini",
    "model": "gemini-2.0-flash",
    "temperature": 0.2,
    "timeout": 120
  }
}
```
*Requires: `GOOGLE_API_KEY` or `GEMINI_API_KEY` environment variable*

## Provider Class Hierarchy

```
Provider (base class)
├─ CommandProvider
│  └─ OllamaProvider (extends CommandProvider)
│     • Adds HTTP API support
│     • Adds model listing
│     • Adds automatic fallback
│
├─ HostedAPIProvider
│  • OpenAI backend
│  • Anthropic backend
│  • Gemini backend
│  • Custom backend support
│
└─ ManualProvider
   • Human-in-the-loop mode
```

## Key Files

- `agent/providers/__init__.py` - Provider factory and routing
- `agent/providers/base.py` - Base Provider interface
- `agent/providers/ollama.py` - Ollama provider with HTTP API
- `agent/providers/api.py` - Cloud API providers (OpenAI, Anthropic, Gemini)
- `agent/providers/command.py` - Command-based providers
- `agent/providers/manual.py` - Manual patch mode
- `agent/providers/keys.py` - Secure key storage
- `agent/run.py` - Main agent loop
- `agent_dashboard/core/real_agent_manager.py` - Dashboard integration

## Testing

Test all providers:
```bash
./test_provider_connection.py
```

Test specific provider:
```bash
# Update agent/config.json first
agent run --max-cycles=1
```

Monitor real-time:
```bash
tail -f agent/state/thinking.jsonl
```
