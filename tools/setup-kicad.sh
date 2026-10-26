#!/bin/bash
# Installs KiCad 10 (official PPA) and pre-caches the kicad-mcp-pro MCP server.
# For the cloud environment's setup script, or run once on Ubuntu 24.04.
set -euo pipefail

KEY=FDA854F61C4D0D9572BB95E5245D5502FAD7A805   # ~kicad PPA signing key (Launchpad API)
mkdir -p /etc/apt/keyrings
curl -fsSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x$KEY" \
  | gpg --dearmor --yes -o /etc/apt/keyrings/kicad.gpg
echo "deb [signed-by=/etc/apt/keyrings/kicad.gpg] https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu noble main" \
  > /etc/apt/sources.list.d/kicad-10.list
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
  kicad kicad-symbols kicad-footprints

kicad-cli version
uvx kicad-mcp-pro version
