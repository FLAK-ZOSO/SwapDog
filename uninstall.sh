sudo systemctl stop swapdog
sudo systemctl disable swapdog
sudo rm /etc/systemd/system/swapdog.service /usr/local/sbin/swapdog.py /etc/swapdog.json
sudo systemctl daemon-reload
