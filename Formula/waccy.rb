# Reference copy — the canonical formula lives in github.com/DecisionNerd/homebrew-tap.
# This file is updated automatically by the release workflow.

class Waccy < Formula
  desc "Intelligent financial modelling for small businesses"
  homepage "https://github.com/DecisionNerd/waccy"
  url "https://github.com/DecisionNerd/waccy/archive/refs/tags/v0.1.0.tar.gz"
  sha256 ""
  license "MIT"

  depends_on "rust" => :build

  def install
    system "cargo", "build", "--release", "--locked",
           "--bin", "waccy",
           "--bin", "waccy-mcp"
    bin.install "target/release/waccy"
    bin.install "target/release/waccy-mcp"

    # Shell completions
    generate_completions_from_executable(bin/"waccy", "completions")
  end

  test do
    system "#{bin}/waccy", "--version"
  end
end
