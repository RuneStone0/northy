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



