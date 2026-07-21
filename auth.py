import hashlib
from database import load_users, save_users
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return hasher.hash(password)

def register_user(username: str, password: str):
    users = load_users()
    current_user = username.lower().strip()

    if not current_user or not password.strip():
        return False, "Username and password cannot be empty."

    if current_user in users:
        return False, "Username already exists."
    
    password_hash = hash_password(password)

    users[current_user] = {
        "password_hash": password_hash,
        "role": "guest"
    }

    save_users(users)
    return True, "New user registered successfully."

def authenticate_user(username: str, password: str):
    users = load_users()
    user_info = users.get(username.lower().strip())

    if not user_info:
        return False, None
    
    stored_hash = user_info["password_hash"]

    try:
        hasher.verify(stored_hash, password)

        if hasher.check_needs_rehash(stored_hash):
            users[username.lower().strip()]["password_hash"] = hasher.hash(password)
            save_users(users)

        return True, user_info["role"]
    
    except (VerifyMismatchError, VerificationError):
        return False, None
    except Exception as e:
        print("Error during authentication:", e)
        return False, None
