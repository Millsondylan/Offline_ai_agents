class Agent < Formula
  include Language::Python::Virtualenv
  desc "Always-on offline-first coding agent with production gates and TUI"
  homepage "https://github.com/Millsondylan/Offline_ai_agents"
  url "https://github.com/Millsondylan/Offline_ai_agents/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "45d00fd9c5b69b8b3db60d930f73c976db01971bde5dc95accf9b829611b3a1a"
  license "Apache-2.0"
  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  service do
    run [opt_bin/"agent", "--headless", "--cooldown-seconds=0"]
    keep_alive true
    environment_variables PATH: std_service_path_env
    log_path var/"log/agent.log"
    error_log_path var/"log/agent.err.log"
  end

  test do
    system "#{bin}/agent", "--version"
    system "#{bin}/agent", "run", "--max-cycles=1"
  end
end
