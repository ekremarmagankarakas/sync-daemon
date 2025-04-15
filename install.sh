#!/bin/bash

SERVICE_NAME=sync_daemon
SCRIPT_PATH=/opt/sync_daemon
CONFIG_DIR=/etc/sync_daemon

echo "Installing sync daemon..."

# Copy files
sudo mkdir -p $SCRIPT_PATH
sudo cp sync_daemon.py $SCRIPT_PATH/
sudo mkdir -p $CONFIG_DIR
sudo cp config.example.json $CONFIG_DIR/config.json

# Set permissions
sudo chmod +x $SCRIPT_PATH/sync_daemon.py

# Set up systemd
sudo cp systemd/sync_daemon.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

echo "Installation complete. Edit config at $CONFIG_DIR/config.json"
