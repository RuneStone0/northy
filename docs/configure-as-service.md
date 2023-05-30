# Install dependencies
```bash
cd northy/
pip install -r requirements.txt
```

# Create Service
Copy `sudo cp scripts/watch.service /etc/systemd/system`

Modify file paths etc. to fit your needs
`sudo nano /etc/systemd/system/watch.service`

# Enable and start the service
```bash
chmod +x boot.sh
sudo systemctl daemon-reload
sudo systemctl enable watch.service
sudo systemctl restart watch.service
```

# Check status
```bash
sudo systemctl status watch.service
screen -ls
screen -r
```

