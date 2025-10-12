# Provider Setup Guide

This guide explains how to connect the agent to real AI models.

## Overview

The agent supports multiple AI providers:

1. **Ollama** (Local, Offline) - Recommended for privacy and offline use
2. **OpenAI** (Cloud API) - GPT-4, GPT-4o-mini, etc.
3. **Anthropic** (Cloud API) - Claude models
4. **Google Gemini** (Cloud API) - Gemini models

## Quick Start

### Option 1: Ollama (Local, Free)

**Recommended for most users - runs locally, no API keys needed**

1. Install Ollama:
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Start Ollama service:
   ```bash
   ollama serve
   ```

3. Download a model (recommended):
   ```bash
   ollama pull deepseek-coder:6.7b-instruct
   ```

4. Configure `agent/config.json`:
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

5. Test the connection:
   ```bash
   python test_provider_connection.py
   ```

**Recommended Ollama Models:**
- `deepseek-coder:6.7b-instruct` - Best for coding (4GB, RECOMMENDED)
- `deepseek-coder:33b` - Higher quality (19GB)
- `llama3` - General purpose (4.7GB)
- `codellama` - Code-focused (3.8GB)

### Option 2: OpenAI (Cloud API)

1. Get an API key from https://platform.openai.com/api-keys

2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. Configure `agent/config.json`:
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

**Recommended Models:**
- `gpt-4o-mini` - Fast and cost-effective
- `gpt-4o` - Most capable
- `gpt-4-turbo` - Good balance

### Option 3: Anthropic Claude (Cloud API)

1. Get an API key from https://console.anthropic.com/

2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

3. Configure `agent/config.json`:
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

**Recommended Models:**
- `claude-3-5-sonnet-20241022` - Best for coding
- `claude-3-opus-20240229` - Most capable
- `claude-3-haiku-20240307` - Fast and economical

### Option 4: Google Gemini (Cloud API)

1. Get an API key from https://makersuite.google.com/app/apikey

2. Set environment variable:
   ```bash
   export GOOGLE_API_KEY="..."
   # or
   export GEMINI_API_KEY="..."
   ```

3. Configure `agent/config.json`:
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

**Recommended Models:**
- `gemini-2.0-flash` - Fast and capable
- `gemini-pro` - Good balance

## Configuration Details

### Ollama Configuration Options

```json
{
  "provider": {
    "type": "ollama",
    "model": "deepseek-coder:6.7b-instruct",
    "base_url": "http://localhost:11434",  // Ollama server URL
    "use_api": true,                       // Use HTTP API (recommended)
    "timeout": 1200,                       // Request timeout in seconds
    "command": {                           // Fallback CLI configuration
      "args": ["bash", "-lc", "bash agent/local/ollama_provider.sh"],
      "timeout": 1200
    }
  }
}
```

### API Provider Configuration Options

```json
{
  "provider": {
    "type": "openai",              // or "anthropic", "gemini"
    "model": "gpt-4o-mini",        // Model name
    "temperature": 0.2,            // 0.0-1.0, lower = more deterministic
    "timeout": 120,                // Request timeout in seconds
    "max_tokens": 8000             // Max response tokens (Anthropic only)
  }
}
```

## Testing Your Configuration

1. Run the connection test:
   ```bash
   python test_provider_connection.py
   ```

2. If successful, start the agent:
   ```bash
   agent
   ```

3. Monitor the logs for connection status

## Switching Providers

You can switch providers at any time by:

1. Updating `agent/config.json`
2. Restarting the agent

Or use the dashboard UI to switch models on the fly.

## Troubleshooting

### Ollama Issues

**"ollama CLI not found on PATH"**
- Install Ollama: `brew install ollama` (macOS) or follow https://ollama.com/download
- Verify: `which ollama`

**"Model not present locally"**
- Pull the model: `ollama pull deepseek-coder:6.7b-instruct`
- List available: `ollama list`

**"Connection refused"**
- Start Ollama service: `ollama serve`
- Check it's running: `curl http://localhost:11434/api/tags`

### API Provider Issues

**"No API key found"**
- Set environment variable: `export OPENAI_API_KEY="sk-..."`
- Or store in keyring: `agent apikey set openai sk-...`

**"API error 401"**
- API key is invalid or expired
- Regenerate key from provider dashboard

**"API error 429"**
- Rate limit exceeded
- Wait and retry, or upgrade your plan

**"Request timeout"**
- Increase timeout in config
- Try a faster model

## Best Practices

1. **For Development**: Use Ollama with `deepseek-coder:6.7b-instruct`
   - Fast, free, runs offline
   - Good code quality
   - No API costs

2. **For Production**: Use Anthropic Claude or OpenAI GPT-4
   - Higher quality output
   - Better reasoning
   - Rate limits apply

3. **For Cost Optimization**:
   - Start with Ollama or `gpt-4o-mini`
   - Monitor token usage
   - Use smaller models for routine tasks

4. **For Best Results**:
   - Keep prompts clear and focused
   - Provide good context in tasks
   - Review and iterate on outputs

## Support

For issues or questions:
- Check logs in `agent/state/thinking.jsonl`
- Review artifacts in `agent/artifacts/cycle_*`
- Open an issue on GitHub

## Advanced: Custom Providers

You can add custom providers by:

1. Extending the `Provider` base class
2. Implementing `generate_patch(prompt, cycle_dir)` method
3. Registering in `agent/providers/__init__.py`

See `agent/providers/base.py` for the interface.
