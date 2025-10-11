import time

from agent_dashboard.core.real_agent_manager import RealAgentManager

if __name__ == "__main__":
    manager = RealAgentManager()
    manager.start()
    while True:
        time.sleep(1)
