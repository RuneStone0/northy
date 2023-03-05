# Project Northy

## Monitor for new Northy Tweets
Watch for new Tweets by Northy every 5 seconds. Tweets are stored in MongoDB.
Higher detection frequency is not possible because of Twitter API throttling.
> timon.py watch

## Send Tweet notifications to Prowl
This service will watch for new tweets in MongoDB every second and send Prowl
notification when a tweet that contains "ALERT" is found. This service is NOT
required for the system to function. Its nice to have only.
> timon.py pushalert


# Configure Startup Scripts
## Run fetch on startup
Open crontab using `sudo crontab -e`. Add the following to the end of the file:
```
@reboot cd $HOME/RuneStone0/northy && venv/bin/python timon.py fetch --limit 200
```

## Configure Background Services
Let's setup the background services. We will create a service to run on boot:
* timon.py fetch --limit 200 (to fetch everything we missed during down time)
* timon.py watch (watch for new tweets)
* timon.py pushalert (service to send push notifications)
The services will start automatically whenever the system is booted.

```
# Add services to system
sudo cp scripts/watch.service /etc/systemd/system/
sudo cp scripts/pushalert.service /etc/systemd/system/

# Set exec permissions
chmod 775 timon.py
chmod 775 scripts/pushalert.sh
chmod 775 scripts/watch.sh

# Register (enable) service
sudo systemctl enable watch
sudo systemctl enable pushalert

# Start services
sudo systemctl start watch
sudo systemctl start pushalert

# Verify they are running
ps aux|grep pyton
```