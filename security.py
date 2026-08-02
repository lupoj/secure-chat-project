# Define a dictionary to map user roles to their corresponding permissions
PERMISSIONS = {
    "guest": ["send_message", "view_users"],
    "moderator": ["send_message", "view_users", "view_logs"],
    "admin": ["send_message", "view_users", "view_logs", "shutdown_server"]
}

# Define a function to check if a user role has permission to perform a specific action
def has_permission(role: str, action: str) -> bool:
    
    return action in PERMISSIONS.get(role, [])