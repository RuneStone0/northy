# Check if the script is running with administrative privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# If not running as admin, relaunch the script with elevated privileges
if (-not $isAdmin) {
    Start-Process powershell.exe -Verb RunAs -ArgumentList ("-File $($MyInvocation.MyCommand.Path) " + $args)
    Exit
}

# Get the session ID for the current user
$sessionId = (query user $env:USERNAME | Select-Object -Skip 1 | ForEach-Object { ($_ -split '\s+')[2] }).Trim()

# Reconnect to the console session using the obtained session ID
tscon.exe $sessionId /dest:console
