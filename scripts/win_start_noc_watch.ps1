echo "cd into /northy"
sleep 2
cd C:\Users\User\Documents\code\RuneOrg\northy

echo "Running git pull"
sleep 2
git pull

echo "Activate virtual environment"
sleep 2
venv\Scripts\activate
sleep 2

echo "Install requirements.txt"
sleep 2
pip install -r .\requirements.txt

# Check if Chrome is running
if (Get-Process -Name "chrome" -ErrorAction SilentlyContinue) {
    Write-Host "Chrome is already open."
} else {
    Write-Host "Chrome is not open. Opening Chrome..."
    Start-Process "chrome"
}

echo "Start watching Windows Notification Center.."
sleep 2
.\cli_noc.py watch

