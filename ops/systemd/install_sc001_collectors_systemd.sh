#!/usr/bin/env bash
set -euo pipefail

REPO="/home/botmarket/botmarketplace-site"

if [[ "$(id -un)" != "botmarket" ]]; then
  echo "Run this script as botmarket (it will use sudo for systemd install)." >&2
  exit 2
fi

cd "$REPO"

echo "Installing systemd unit files..."
sudo install -m 0644 ops/systemd/sc001-b13c-liquidation.service /etc/systemd/system/sc001-b13c-liquidation.service
sudo install -m 0644 ops/systemd/sc001-b14a-p0.service /etc/systemd/system/sc001-b14a-p0.service
sudo systemctl daemon-reload
sudo systemctl enable sc001-b13c-liquidation.service sc001-b14a-p0.service

echo "Installed and enabled for boot. Services are NOT started by this installer."
