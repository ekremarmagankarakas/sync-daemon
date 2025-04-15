# Sync Daemon

A lightweight Linux background service to periodically sync files from `/home/username/` to a custom destination using `rsync`.

## Features

- Runs as a systemd service
- Configurable sync interval and destination path
- Uses `rsync` for efficient syncing
- Logs all operations to `/var/log/sync_daemon.log`

## Installation

```bash
git clone https://github.com/yourusername/sync-daemon.git
cd sync-daemon
sudo ./install.sh