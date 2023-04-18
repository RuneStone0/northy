#!/bin/bash
screen_name="northy"
folder_name="/home/rune/RuneStone0/northy"

# Change CWD
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

# Fetch latest Tweets
echo "Fetching latest Tweets..."
python main.py fetch --limit 200

# Create new screen
echo "Creating new screen..."
screen -dmS $screen_name  # Start new screen session, detached, with name $screen_name
screen -S $screen_name -X stuff "python main.py watch$(printf '\r')"
screen -ls
