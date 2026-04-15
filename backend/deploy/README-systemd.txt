# Install systemd unit
sudo cp /opt/avtoritet/backend/deploy/avtoritet-assistant.service /etc/systemd/system/avtoritet-assistant.service
sudo systemctl daemon-reload
sudo systemctl enable avtoritet-assistant
sudo systemctl start avtoritet-assistant

# Check status/logs
sudo systemctl status avtoritet-assistant --no-pager
sudo journalctl -u avtoritet-assistant -f

# Restart after code/env changes
sudo systemctl restart avtoritet-assistant
