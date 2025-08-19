#!/bin/bash
set -e

echo "Installing dependencies..."
sudo pip3 install -r requirements.txt

echo "Installing swapdog.py to /usr/local/sbin/"
sudo install -m 744 swapdog.py /usr/local/sbin/swapdog.py

echo "Installing swapdog.json to /etc/"
sudo install -m 644 swapdog.json /etc/swapdog.json

echo "Installing swapdog.service to /etc/systemd/system/"
sudo install -m 644 swapdog.service /etc/systemd/system/swapdog.service

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling swapdog service..."
sudo systemctl enable swapdog.service

echo "Starting swapdog service..."
sudo systemctl start swapdog.service

echo "Installation complete."
echo "You can check the status of the service with: sudo systemctl status swapdog.service"
