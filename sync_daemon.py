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

def sync(src, dest, excludes=None):
    try:
        cmd = ["rsync", "-avh", "--delete"]
        
        if excludes:
            for pattern in excludes:
                cmd.extend(["--exclude", pattern])
        
        cmd.extend([src, dest])
        subprocess.run(cmd, check=True)
        logging.info(f"Synced {src} to {dest}")
    except subprocess.CalledProcessError as e:
        logging.error(f"rsync failed: {e}")

def get_task_hash(config):
    """Generate a hash of the task configuration to detect changes"""
    if "tasks" in config:
        # For multi-task config, use the length and source/destination paths
        tasks_hash = len(config["tasks"])
        for task in config["tasks"]:
            tasks_hash = hash((tasks_hash, task["source"], task["destination"], 
                              task.get("interval_minutes", 30)))
        return tasks_hash
    else:
        # For single task config
        return hash((config["source"], config["destination"], 
                   config.get("interval_minutes", 30)))

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
                for i, task in enumerate(tasks):
                    next_run = current_time
                    heapq.heappush(task_queue, (next_run, i, task))
                logging.info(f"Loaded {len(tasks)} tasks from config")
            else:
                # Legacy single task configuration
                task = {
                    "source": config["source"],
                    "destination": config["destination"],
                    "interval_minutes": config.get("interval_minutes", 30),
                    "excludes": config.get("excludes", [])
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
        
        sync(src, dest, excludes)
        
        # Schedule the next run
        next_run = datetime.now() + timedelta(minutes=interval)
        heapq.heappush(task_queue, (next_run, task_id, task))
        
        logging.info(f"Task {task_id}: Next sync in {interval} minutes at {next_run}")
        
        # If queue is empty, sleep for a short time before reloading config
        if not task_queue:
            time.sleep(10)

if __name__ == "__main__":
    main()
