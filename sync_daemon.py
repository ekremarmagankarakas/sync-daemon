import os
import time
import json
import subprocess
import logging

CONFIG_PATH = "/etc/sync_daemon/config.json"

logging.basicConfig(
    filename="/var/log/sync_daemon.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

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

def main():
    while True:
        config = load_config()
        src = os.path.expanduser(config["source"])
        dest = os.path.expanduser(config["destination"])
        interval = config.get("interval_minutes", 30)
        excludes = config.get("excludes", [])
        
        sync(src, dest, excludes)
        logging.info(f"Next sync in {interval} minutes")
        time.sleep(interval * 60)

if __name__ == "__main__":
    main()
