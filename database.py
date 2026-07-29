import json
import os
import uuid
from datetime import datetime

USERS_FILE = "users.json"
SHADOW_FILE = "shadow.json"

DEFAULT_TIMESTAMP = "2026-01-01T00:00:00Z"

# Default users with hashed passwords and roles
# Passwords in plaintext
#
# administrator: Password1!
# manager: Password2!
# user: Password3!
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

def load_users():
    if not os.path.exists(USERS_FILE):
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_USERS

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_shadow():
    if not os.path.exists(SHADOW_FILE):
        save_shadow(DEFAULT_SHADOW)
        return DEFAULT_SHADOW
    try:
        with open(SHADOW_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return DEFAULT_SHADOW

def save_shadow(data):
    with open(SHADOW_FILE, "w") as f:
        json.dump(data, f, indent=4)

