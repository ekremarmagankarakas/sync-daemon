#!/bin/bash
# Setup a local test environment for sync-daemon

# Create test directories
mkdir -p ~/sync_test/source1
mkdir -p ~/sync_test/source2
mkdir -p ~/sync_test/dest

# Create some test files
echo "Test file 1" > ~/sync_test/source1/test1.txt
echo "Test file 2" > ~/sync_test/source1/test2.txt
echo "Test file 3" > ~/sync_test/source2/test3.txt

# Create local config file for testing
cat > ~/sync_test/config.json << EOF
{
  "tasks": [
    {
      "source": "$HOME/sync_test/source1/",
      "destination": "$HOME/sync_test/dest/source1/",
      "interval_minutes": 1,
      "excludes": ["*.tmp"]
    },
    {
      "source": "$HOME/sync_test/source2/",
      "destination": "$HOME/sync_test/dest/source2/",
      "interval_minutes": 2,
      "excludes": ["*.tmp"]
    }
  ]
}
EOF

# Create local log file
touch ~/sync_test/sync_daemon.log

echo "Test environment created at ~/sync_test/"
echo "To run the daemon in test mode, use the modified script with command line arguments"