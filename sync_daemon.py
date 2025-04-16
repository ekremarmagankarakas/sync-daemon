import os
import time
import json
import subprocess
import logging
import heapq
import argparse
from datetime import datetime, timedelta

# Default paths
DEFAULT_CONFIG_PATH = "/etc/sync_daemon/config.json"
DEFAULT_LOG_PATH = "/var/log/sync_daemon.log"

# Parse command line arguments
parser = argparse.ArgumentParser(description='Run sync daemon with custom config and log paths')
parser.add_argument('--config', help='Path to config file', default=DEFAULT_CONFIG_PATH)
parser.add_argument('--log', help='Path to log file', default=DEFAULT_LOG_PATH)
args = parser.parse_args()

CONFIG_PATH = args.config

logging.basicConfig(
    filename=args.log,
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# Also log to console for testing
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger('').addHandler(console)

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def sync(src, dest, excludes=None, keep_backups=2, prune_old_backups=True):
    try:
        # Create timestamp for backup folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dest = os.path.join(dest, timestamp)
        
        # Create backup directory
        os.makedirs(backup_dest, exist_ok=True)
        
        # Run rsync to backup folder
        cmd = ["rsync", "-avh", "--delete"]
        
        if excludes:
            for pattern in excludes:
                cmd.extend(["--exclude", pattern])
        
        cmd.extend([src, backup_dest])
        subprocess.run(cmd, check=True)
        logging.info(f"Synced {src} to {backup_dest}")
        
        # Retain only the most recent backups if pruning is enabled
        if prune_old_backups:
            manage_backup_retention(dest, keep_backups)
            logging.info(f"Backup retention policy: keeping {keep_backups} most recent backups")
        else:
            logging.info("Backup retention policy: keeping all backups")
    except subprocess.CalledProcessError as e:
        logging.error(f"rsync failed: {e}")
    except Exception as e:
        logging.error(f"Backup failed: {e}")

def manage_backup_retention(backup_dir, keep_count=2):
    """Keep only the specified number of most recent backups."""
    try:
        # List all backup directories
        backup_folders = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path) and item.replace("_", "").isdigit():
                # Only consider timestamp-named folders (YYYYmmdd_HHMMSS format)
                backup_folders.append(item_path)
        
        # Sort backups by creation time (newest first)
        backup_folders.sort(reverse=True)
        
        # Remove older backups beyond the keep count
        if len(backup_folders) > keep_count:
            for old_backup in backup_folders[keep_count:]:
                logging.info(f"Removing old backup: {old_backup}")
                subprocess.run(["rm", "-rf", old_backup], check=True)
    except Exception as e:
        logging.error(f"Error managing backup retention: {e}")

def get_task_hash(config):
    """Generate a hash of the task configuration to detect changes"""
    if "tasks" in config:
        # For multi-task config, use the length and source/destination paths
        tasks_hash = len(config["tasks"])
        for task in config["tasks"]:
            tasks_hash = hash((tasks_hash, task["source"], task["destination"], 
                              task.get("interval_minutes", 30),
                              task.get("keep_backups", 2),
                              task.get("prune_old_backups", True),
                              task.get("enabled", True)))
        return tasks_hash
    else:
        # For single task config
        return hash((config["source"], config["destination"], 
                   config.get("interval_minutes", 30),
                   config.get("keep_backups", 2),
                   config.get("prune_old_backups", True),
                   True))  # Legacy tasks are always enabled

def main():
    # Priority queue of (next_run_time, task_id, task_config)
    task_queue = []
    last_config_hash = None
    
    while True:
        config = load_config()
        current_time = datetime.now()
        current_config_hash = get_task_hash(config)
        
        # Check if we need to rebuild the queue (first run, config reload, or config changed)
        if not task_queue or current_config_hash != last_config_hash:
            logging.info("Config changed or initial load, rebuilding task queue")
            # Clear the existing queue
            task_queue = []
            last_config_hash = current_config_hash
            
            # Handle both single task and multiple tasks configurations
            if "tasks" in config:
                tasks = config["tasks"]
                enabled_tasks = 0
                for i, task in enumerate(tasks):
                    # Skip disabled tasks
                    if not task.get("enabled", True):
                        logging.info(f"Task {i} is disabled, skipping")
                        continue
                    
                    next_run = current_time
                    heapq.heappush(task_queue, (next_run, i, task))
                    enabled_tasks += 1
                
                logging.info(f"Loaded {enabled_tasks} enabled tasks from config (total: {len(tasks)})")
            else:
                # Legacy single task configuration
                # For backward compatibility, legacy tasks are always enabled
                task = {
                    "source": config["source"],
                    "destination": config["destination"],
                    "interval_minutes": config.get("interval_minutes", 30),
                    "excludes": config.get("excludes", []),
                    "enabled": True
                }
                heapq.heappush(task_queue, (current_time, 0, task))
                logging.info("Loaded single task from legacy config")
        
        # Get the next task to run
        next_run, task_id, task = heapq.heappop(task_queue)
        
        # If it's not time to run this task yet, wait
        if next_run > current_time:
            # Calculate how long to wait (max 60 seconds to check for config changes)
            wait_time = min(60, (next_run - current_time).total_seconds())
            time.sleep(wait_time)
            # Re-add the task without running it and continue
            heapq.heappush(task_queue, (next_run, task_id, task))
            continue
        
        # Run the task
        src = os.path.expanduser(task["source"])
        dest = os.path.expanduser(task["destination"])
        interval = task.get("interval_minutes", 30)
        excludes = task.get("excludes", [])
        keep_backups = task.get("keep_backups", 2)
        prune_old_backups = task.get("prune_old_backups", True)
        
        sync(src, dest, excludes, keep_backups, prune_old_backups)
        
        # Schedule the next run
        next_run = datetime.now() + timedelta(minutes=interval)
        heapq.heappush(task_queue, (next_run, task_id, task))
        
        logging.info(f"Task {task_id}: Next sync in {interval} minutes at {next_run}")
        
        # If queue is empty, sleep for a short time before reloading config
        if not task_queue:
            time.sleep(10)

if __name__ == "__main__":
    main()
