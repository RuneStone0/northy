# Parse the .env file into a hashtable
$envVars = @{}
Get-Content .\.env | ForEach-Object {
    if ($_ -match '^\s*([^#].+?)\s*=\s*(.+)\s*$') {
        $name, $value = $matches[1], $matches[2]
        $envVars[$name] = $value
    }
}

# Get the MONGODB_CONN variable
$mongoConn = $envVars["MONGODB_CONN"]

# Create a folder for the backup
$folderName = Get-Date -Format "yyyy-MM-dd-HH-mm-ss"

# Run the backup
.\backups\mongodump.exe --uri=$mongoConn --db=northy --collection=tweets --out=backups/$folderName/

# Copy backups/$folderName/tweets.bson to backups/tweets.bson
Copy-Item backups/$folderName/northy/tweets.bson backups/tweets.bson
