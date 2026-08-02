import json
import os
import uuid
from datetime import datetime

# Define the file paths for storing user data and shadow password data
USERS_FILE = "users.json"
SHADOW_FILE = "shadow.json"

# Define a default timestamp for user creation and last login
DEFAULT_TIMESTAMP = "2026-01-01T00:00:00Z"

# Default users with hashed passwords and roles
DEFAULT_USERS = {
    "administrator": {
        "username": "administrator",
        "user_id": "usr_admin01",
        "display_name": "System Administrator",
        "role": "admin",
        "created_at": DEFAULT_TIMESTAMP,
        "last_login": None
    },
    "manager": {
        "username": "manager",
        "user_id": "usr_mgr02",
        "display_name": "Manager",
        "role": "moderator",
        "created_at": DEFAULT_TIMESTAMP,
        "last_login": None
    },
    "user": {
        "username": "user",
        "user_id": "usr_guest03",
        "display_name": "Guest User",
        "role": "guest",
        "created_at": DEFAULT_TIMESTAMP,
        "last_login": None
    }
}

# Default shadow data with hashed passwords for each user
DEFAULT_SHADOW = {
    "administrator": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$NkFnMGtQaVdFeU9yYU5nSQ$4oDP3baGKtdN/3VsSvQtjA"
    },
    "manager": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$RHR0S1AwbnRvdHNhZWp4TQ$6Md3PJTrOkKQZXPtBd7+JQ"
    },
    "user": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$ZVVsTERCTDJLdGZCUzlWeg$Vwvu/B8p5LQpS5x9aq5lgw"
    }
}

# Load users from the USERS_FILE if it exists, otherwise save the DEFAULT_USERS to the file and return them
def load_users():

    # Check if the USERS_FILE exists, if not, save the DEFAULT_USERS to the file and return them
    if not os.path.exists(USERS_FILE):

        save_users(DEFAULT_USERS)
        return DEFAULT_USERS

    # Attempt to load users from the USERS_FILE, and handle any exceptions that may occur during file reading or JSON parsing
    try:

        # Open the USERS_FILE in read mode and load the JSON data into a Python dictionary
        with open(USERS_FILE, "r") as f:
            return json.load(f)
        
    except Exception: 

        return DEFAULT_USERS    # If an error occurs while loading users, return the DEFAULT_USERS as a fallback

# Save the provided user data to the USERS_FILE in JSON format with indentation for readability
def save_users(data):

    # Open the USERS_FILE in write mode and dump the provided user data as JSON with an indentation of 4 spaces for better readability
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load shadow data from the SHADOW_FILE if it exists, otherwise save the DEFAULT_SHADOW to the file and return it
def load_shadow():

    if not os.path.exists(SHADOW_FILE):
        save_shadow(DEFAULT_SHADOW)
        return DEFAULT_SHADOW
    try:
        with open(SHADOW_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return DEFAULT_SHADOW

# Save the provided shadow data to the SHADOW_FILE in JSON format with indentation for readability
def save_shadow(data):

    # Open the SHADOW_FILE in write mode and dump the provided shadow data as JSON with an indentation of 4 spaces for better readability
    with open(SHADOW_FILE, "w") as f:
        json.dump(data, f, indent=4)

