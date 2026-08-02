import hashlib
import uuid
import time
from datetime import datetime
from database import load_users, save_users, load_shadow, save_shadow
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Initialize the PasswordHasher instance for hashing and verifying passwords
hasher = PasswordHasher()

# Define a dictionary to track failed login attempts and lockout information for each user
FAILED_ATTEMPTS = {}

# Define a function to determine the lockout delay based on the number of failed attempts
def get_lockout_delay(attempts: int) -> int:

    # Return the lockout delay in seconds based on the number of failed attempts
    if attempts < 3:

        return 0
    
    elif attempts == 3:

        return 10
    
    elif attempts == 4:

        return 30
    
    else:

        return 60

# Define a function to hash a password using the PasswordHasher instance
def hash_password(password: str) -> str:

    return hasher.hash(password)

# Define a function to register a new user with a username, password, and optional display name
def register_user(username: str, password: str, display_name: str = None):

    # Load the existing users and shadow data from the respective files
    users = load_users()
    shadow = load_shadow()

    # Convert the username to lowercase and strip whitespace for consistency
    current_user = username.lower().strip()

    # Check if the username or password is empty, and return an error message if so
    if not current_user or not password.strip():

        return False, "Username and password cannot be empty."

    # Check if the username already exists in the users dictionary, and return an error message if so
    if current_user in users:

        return False, "Username already exists."

    # Hash the password using the hash_password function and get the current timestamp in UTC format
    password_hash = hash_password(password)
    now_timestamp = datetime.utcnow().isoformat()

    # Create a new user entry in the users dictionary with the provided username, display name, role, and timestamps
    users[current_user] = {
        "username": current_user,
        "user_id": str(uuid.uuid4())[:8],
        "display_name": display_name if display_name else username.strip(),
        "role": "guest",
        "created_at": now_timestamp,
        "last_login": None
    }

    # Create a new shadow entry in the shadow dictionary with the hashed password for the user
    shadow[current_user] = {
        "password_hash": password_hash
    }

    # Save the updated users and shadow data back to their respective files
    save_users(users)
    save_shadow(shadow)

    # Return a success message indicating that the new user has been registered successfully
    return True, "New user registered successfully."

# Define a function to authenticate a user with a username and password
def authenticate_user(username: str, password: str):

    # Load the existing users and shadow data from the respective files
    users = load_users()
    shadow = load_shadow()

    # Convert the username to lowercase and strip whitespace for consistency
    current_user = username.lower().strip()

    # Check if the username or password is empty, and return an error message if so
    user_info = users.get(current_user)
    shadow_info = shadow.get(current_user)
    if not user_info or not shadow_info:
        
        return False, None, "Incorrect username or password."   # Return a generic error message to avoid revealing whether the username exists

    # Define a dictionary to track failed login attempts and lockout information for each user
    lock_data = FAILED_ATTEMPTS.get(current_user, {"failed_attempts": 0, "lockout_until": 0})
    current_time = time.time()  # Get the current time in seconds

    # Check if the user is currently locked out due to too many failed login attempts, and return an error message with the remaining lockout time if so
    if current_time < lock_data["lockout_until"]:

        rem_sec = int(lock_data["lockout_until"] - current_time)    # Calculate the remaining lockout time in seconds
        return False, None, f"You are locked out. Try again in {rem_sec} seconds."  # Return an error message indicating the remaining lockout time

    # Retrieve the stored password hash for the user from the shadow data
    stored_hash = shadow_info["password_hash"]

    # Attempt to verify the provided password against the stored hash using the PasswordHasher instance, and handle any exceptions that may occur during verification
    try:

        hasher.verify(stored_hash, password)    # Verify the provided password against the stored hash using the PasswordHasher instance

        # If the current user has failed attempts recorded in the FAILED_ATTEMPTS dictionary, remove their entry to reset the failed attempts count
        if current_user in FAILED_ATTEMPTS:

            del FAILED_ATTEMPTS[current_user]

        # If the password needs to be rehashed, rehash it and update the shadow data with the new hash, then save the updated shadow data to the file
        if hasher.check_needs_rehash(stored_hash):

            shadow[current_user]["password_hash"] = hasher.hash(password)   # Rehash the password and update the shadow data with the new hash
            save_shadow(shadow)     # Save the updated shadow data to the file

        # Update the last login timestamp for the user in the users dictionary and save the updated users data to the file
        users[current_user]["last_login"] = datetime.utcnow().isoformat()
        save_users(users)

        return True, user_info["role"], "Login success!"    # Return a success message indicating that the user has been authenticated successfully, along with their role
    
    except (VerifyMismatchError, VerificationError):    # Handle the case where the provided password does not match the stored hash, and update the failed attempts count and lockout information for the user

        # Increment the failed attempts count for the current user and calculate the lockout delay based on the number of failed attempts, then update the lockout information in the FAILED_ATTEMPTS dictionary
        attempts = lock_data["failed_attempts"] + 1
        lock_delay = get_lockout_delay(attempts)
        lockout_until = current_time + lock_delay

        # Determine the appropriate error message to return based on whether the user is locked out or has remaining attempts before lockout
        if lock_delay > 0:

            message = f"Incorrect password: Too many failed attempts. Account is locked for {lock_delay} seconds."

        else:

            message = f"Incorrect username or password. ({3 - attempts} attempt(s) left before account lockout)"

        FAILED_ATTEMPTS[current_user] = {"failed_attempts": attempts, "lockout_until": lockout_until}   # Update the FAILED_ATTEMPTS dictionary with the new failed attempts count and lockout information for the current user

        return False, None, message     # Return an error message indicating that the provided password is incorrect, along with the number of remaining attempts before account lockout or the lockout duration if applicable
    
    except Exception as e:  # Handle any other unexpected exceptions that may occur during authentication and return a generic error message to avoid revealing sensitive information
        
        print("Error during authentication:", e)
        return False, None, "Error has occurred"
