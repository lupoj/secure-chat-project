import hashlib
import uuid
from datetime import datetime
from database import load_users, save_users, load_shadow, save_shadow
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return hasher.hash(password)

def register_user(username: str, password: str, display_name: str = None):
    users = load_users()
    shadow = load_shadow()
    current_user = username.lower().strip()

    if not current_user or not password.strip():
        return False, "Username and password cannot be empty."

    if current_user in users:
        return False, "Username already exists."
    
    password_hash = hash_password(password)
    now_timestamp = datetime.utcnow().isoformat()

    users[current_user] = {
        "username": current_user,
        "user_id": str(uuid.uuid4())[:8],
        "display_name": display_name if display_name else username.strip(),
        "role": "guest",
        "created_at": now_timestamp,
        "last_login": None
    }

    shadow[current_user] = {
        "password_hash": password_hash
    }

    save_users(users)
    save_shadow(shadow)

    return True, "New user registered successfully."

def authenticate_user(username: str, password: str):
    users = load_users()
    shadow = load_shadow()

    current_user = username.lower().strip()
    user_info = users.get(current_user)
    shadow_info = shadow.get(current_user)

    if not user_info or not shadow_info:
        return False, None
    
    stored_hash = shadow_info["password_hash"]

    try:
        hasher.verify(stored_hash, password)

        if hasher.check_needs_rehash(stored_hash):
            shadow[current_user]["password_hash"] = hasher.hash(password)
            save_shadow(shadow)

        users[current_user]["last_login"] = datetime.utcnow().isoformat()
        save_users(users)

        return True, user_info["role"]
    
    except (VerifyMismatchError, VerificationError):
        return False, None
    except Exception as e:
        print("Error during authentication:", e)
        return False, None
