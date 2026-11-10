#!/bin/bash
# Kill leftover Python/ZMQ processes and clear temp sockets.
echo "Refreshing ZMQ / Python processes..."
sudo pkill -f python || true
sudo rm -rf /tmp/zmq* /var/tmp/zmq* 2>/dev/null || true
echo "Done."
