#!/bin/bash
folder_name="/home/rune/RuneStone0/northy"

# Change CWD
echo "Changing CWD to $folder_name"
cd $folder_name

# Kill all existing processes with "python main.py watch" command line
processes=$(pgrep -fl "python main.py watch")
for process in $processes; do
  # Extract the process ID from the process line
  process_id=$(echo $process | awk '{print $1}')
  echo "Killing process with ID: $process_id"
  # Kill the process
  kill $process_id
done
echo "All processes with 'python main.py watch' command line have been killed."

# Stash and pull latest changes
echo "Stashing and pulling latest changes..."
git stash
git pull

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Fetch latest Tweets
echo "Fetching latest Tweets..."
python main.py fetch --limit 200

# Run the Python program in the background
echo "Starting Northy Watcher in the background..."
nohup python main.py watch > /dev/null 2>&1 &

exit 0