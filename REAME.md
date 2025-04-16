# Sync Daemon

A lightweight Linux background service to periodically sync files from multiple sources to custom destinations using `rsync`.

## Features

- Runs as a systemd service
- Support for multiple sync tasks with different intervals
- Configurable sync interval and destination path for each task
- Uses `rsync` for efficient syncing
- Logs all operations to `/var/log/sync_daemon.log`

## Installation

```bash
git clone https://github.com/yourusername/sync-daemon.git
cd sync-daemon
sudo ./install.sh
```

## Configuration

Edit the configuration file at `/etc/sync_daemon/config.json`. 

### Multiple Tasks Configuration

You can configure multiple sync tasks with different intervals:

```json
{
  "tasks": [
    {
      "source": "/home/username/documents/",
      "destination": "/mnt/backup_drive/documents/",
      "interval_minutes": 15,
      "excludes": ["*.tmp", ".cache/"]
    },
    {
      "source": "/home/username/pictures/",
      "destination": "/mnt/backup_drive/pictures/",
      "interval_minutes": 60,
      "excludes": ["*.tmp"]
    }
  ]
}
```

Each task requires:
- `source`: Directory to sync from (will be expanded with ~ if needed)
- `destination`: Directory to sync to (will be expanded with ~ if needed)
- `interval_minutes`: Time between syncs in minutes 
- `excludes`: List of patterns to exclude (optional)

### Modifying Configuration While Running

You can modify the configuration file while the daemon is running:

1. To change the interval of an existing task: edit the `interval_minutes` value
2. To add a new task: add a new object to the `tasks` array
3. To remove a task: delete its object from the `tasks` array

The daemon checks for configuration changes every 60 seconds and automatically rebuilds its task queue when changes are detected. Changes take effect immediately without requiring a service restart.