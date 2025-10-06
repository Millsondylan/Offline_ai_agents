class Agent < Formula
  include Language::Python::Virtualenv
  desc "Always-on offline-first coding agent with production gates and TUI"
  homepage "https://github.com/Millsondylan/Offline_ai_agents"
  url "https://github.com/Millsondylan/Offline_ai_agents/archive/refs/tags/v0.2.5.tar.gz"
  sha256 "5c2127966b820cc2f12308cef0c6265a6dc7f890eb364d8cd06bd666af652337"
  license "Apache-2.0"
  depends_on "python@3.12"

  def install
    virtualenv_create(libexec, "python3.12")
    system libexec/"bin/pip", "install", "-v", "--no-deps",
           "--ignore-installed",
           buildpath
    system libexec/"bin/pip", "install", "-v",
           "textual>=0.47.0",
           "watchdog>=3.0.0",
           "requests>=2.31.0",
           "keyring>=24.0.0"
    bin.install_symlink libexec/"bin/agent"
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
