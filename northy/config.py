import os
from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),
    #**os.environ,  # override loaded values with environment variables
}

# Convert string representation of boolean to boolean
production = config["PRODUCTION"]
if production.lower() == "true":
    config["PRODUCTION"] = True
elif production.lower() == "false":
    config["PRODUCTION"] = False
else:
    raise ValueError("Invalid string representation.")
