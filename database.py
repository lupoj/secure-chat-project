import json
import os

DB_FILE = "users.json"

# Default users with hashed passwords and roles
# Passwords in plaintext
#
# administrator: Password1!
# manager: Password2!
# user: Password3!
DEFAULT_USERS = {
    "administrator": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$NkFnMGtQaVdFeU9yYU5nSQ$4oDP3baGKtdN/3VsSvQtjA",
        "role": "admin"
    },
    "manager": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$RHR0S1AwbnRvdHNhZWp4TQ$6Md3PJTrOkKQZXPtBd7+JQ",
        "role": "moderator"
    },
    "user": {
        "password_hash": "$argon2id$v=19$m=64,t=3,p=4$ZVVsTERCTDJLdGZCUzlWeg$Vwvu/B8p5LQpS5x9aq5lgw",
        "role": "guest"
    }
}

def load_users():
    if not os.path.exists(DB_FILE):
        save_users(DEFAULT_USERS)
        return DEFAULT_USERS
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_USERS

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

