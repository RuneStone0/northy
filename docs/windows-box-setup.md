# On Windows

# Install Windows PowerToys
1. From the Microsoft Store, install PowerToys
2. Open PowerToys
3. Go to Awake
4. Enable Awake
5. Set Mode to "Keep awake indefinitely"
6. Enable "Keep screen on"

## Run Github Actions inside WSL on Windows
Assuming Github Actions is installed in WSL, run:
```PowerShell
northy\scripts\win_start_gha.ps1
```

## Start watching Notification Center
```PowerShell
northy\scripts\win_start_noc_watch.ps1
```

## Exit Windows without killing console
RDP sessions will become "deactivated" when there is not a connection to them. Programs will still run, but anything that depends on GUI interaction will break badly. To "convert" a terminal session into a console session before terminating the RDP session by running the following command: `for /f "skip=1 tokens=3" %s in ('query user %USERNAME%') do (tscon.exe %s /dest:console)`

More info here: 
https://stackoverflow.com/questions/15887729/can-the-gui-of-an-rdp-session-remain-active-after-disconnect

Alternatively run this script:
```PowerShell
northy\scripts\win_exit_rdp.ps1
```
