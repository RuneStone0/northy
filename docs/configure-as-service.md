# Install dependencies
```
cd northy/
pip install -r requirements.txt
```

# Create Service
Create a service file:

`nano /etc/systemd/system/watch.service`

Insert the following (update the paths to match your setup):

```
[Unit]
Description=Northy Watch Service
After=network.target

[Service]
Type=idle
Restart=always
RestartSec=1
User=rune
ExecStart=/usr/bin/python3 /home/rune/RuneStone0/northy/main.py watch
ExecStartPre=/bin/sleep 30

[Install]
WantedBy=multi-user.target
```

# Enable and start the service
```bash
sudo systemctl enable watch.service
sudo systemctl start watch.service
```
