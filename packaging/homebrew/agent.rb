class Agent < Formula
  include Language::Python::Virtualenv
  desc "Always-on offline-first coding agent with production gates and TUI"
  homepage "https://github.com/Millsondylan/Offline_ai_agents"
  url "https://github.com/Millsondylan/Offline_ai_agents/archive/refs/tags/v0.2.7.tar.gz"
  sha256 "411fc9bcf41c3af982a76771dde3890c2fffb6ee42a87dd10b4f3a9812e9fed3"
  license "Apache-2.0"
  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources using: "python@3.12"
  end

  def post_install
    # Install TUI dependencies
    system libexec/"bin/python", "-m", "pip", "install", "--quiet",
           "textual>=0.47.0",
           "watchdog>=3.0.0",
           "requests>=2.31.0",
           "keyring>=24.0.0"
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
