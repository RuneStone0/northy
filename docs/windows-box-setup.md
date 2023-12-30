# On Windows

# Install Windows PowerToys
1. From the Microsoft Store, install PowerToys
2. Open PowerToys
3. Go to Awake
4. Enable Awake
5. Set Mode to "Keep awake indefinitely"
6. Enable "Keep screen on"

## Run Github Actions inside WSL on Windows
```bash
cd /home/actions-runner
./run.sh
```

## Start Notification Center for new Tweets
```cmd
PowerShell -Command "Set-ExecutionPolicy Unrestricted" >> "%TEMP%\StartupLog.txt" 2>&1
PowerShell %USERPROFILE%\Documents\code\RuneOrg\northy\scripts\noc.ps1
```

## Exit Windows without killing console
When you RDP into a Windows box, you can exit the RDP session without killing 
the console, thus keeping the Windows Notifications Center "alive". This is 
required to keep the script (noc.py) receiving notifications from Twitter.

More info here: 
https://stackoverflow.com/questions/15887729/can-the-gui-of-an-rdp-session-remain-active-after-disconnect

```cmd
PowerShell -Command "Set-ExecutionPolicy Unrestricted" >> "%TEMP%\StartupLog.txt" 2>&1
PowerShell %USERPROFILE%\Documents\code\RuneOrg\northy\scripts\noc.ps1
```
