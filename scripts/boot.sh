#!/bin/bash

# Change CWD
folder_name="/home/rune/RuneStone0/northy"
echo "Changing CWD to $folder_name"
cd $folder_name

# Stash and pull latest changes
echo "Stashing and pulling latest changes..."
git stash
git pull

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Kill existing screens
echo "Killing existing screens..."
detached_sessions=$(screen -ls | grep Detached | cut -d. -f1 | awk '{print $1}')
if [ -n "$detached_sessions" ]; then
  echo "$detached_sessions" | xargs kill
else
  echo "No detached screen sessions found."
fi

# Create new screens
echo "Creating new screen..."
screen_alerts="alerts"
screen -dmS $screen_alerts  # Start new screen session, detached, with name $screen_name
screen -S $screen_alerts -X stuff "python main.py watch --alerts $(printf '\r')"

screen_tweets="tweets"
screen -dmS $screen_tweets  # Start new screen session, detached, with name $screen_name
screen -S $screen_tweets -X stuff "python main.py watch  --tweets $(printf '\r')"

screen -ls
