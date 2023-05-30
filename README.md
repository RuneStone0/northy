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

# Saxo Bank
## Configure Account Timeout
Login to the Saxo Account.
Go to Profile > Settings > Login & Security > Automatic Logout > Max


# TODO
* Make sure `python tests/test_TradeSignal.py` is using in memory DB to increase speed
* Use Twitter API v2 instead of v1. (tweepy.API  -->  tweepy.Client)
* Setup a service to run on boot
* Unit testing & Code coverage
* Add allin command with threading to start watch2 + twitter + pushalert
* Make "Close Position" work
* Move config to JSON file
* Move SaxoTrader conf to config file
* Prevent Twitter API suspension, only fetch when markets are open

## Long-term
* Look into using ML to parse alert tweets
* Support multiple "customers" within my own SaxoBank account
* Support TD365

