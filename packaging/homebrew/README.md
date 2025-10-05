Homebrew Tap and Service
========================

- Tap and install:

  ```bash
  brew tap YOURORG/agent
  brew install agent
  ```

- Run as a service:

  ```bash
  brew services start agent
  ```

The service launches `agent --headless --cooldown-seconds=0` and writes logs to Homebrew’s log directory.

## Linux systemd sample

For Linux hosts, create `/etc/systemd/system/agent.service` containing:

```ini
[Unit]
Description=Agent 24x7 loop
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/agent
ExecStart=/opt/agent/venv/bin/agent --headless --cooldown-seconds=0
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/agent

[Install]
WantedBy=multi-user.target
```

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agent.service
```
