echo "cd into /northy"
sleep 1
cd C:\Users\User\Documents\code\RuneOrg\northy

echo "Running git pull"
sleep 1
git pull

echo "Activate virtual environment"
sleep 1
venv\Scripts\activate
sleep 1

echo "Upgrade pip"
sleep 1
python.exe -m pip install --upgrade pip
sleep 1

echo "Install requirements.txt"
sleep 1
pip install -r .\requirements.txt

# Check if Chrome is running
if (Get-Process -Name "chrome" -ErrorAction SilentlyContinue) {
    Write-Host "Chrome is already open."
} else {
    Write-Host "Chrome is not open. Opening Chrome..."
    Start-Process "chrome"
}

echo "Start watching Signals.."
sleep 1
[console]::Title = ".\cli_signal.py --prod watch"
.\cli_signal.py --prod watch

