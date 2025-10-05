Homebrew Tap and Service

- Tap and install:

  brew tap YOURORG/agent && brew install agent

- Run as a service:

  brew services start agent

The service launches `agent --headless --cooldown-seconds=0` and writes logs to Homebrew’s log directory.

