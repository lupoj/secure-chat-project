PERMISSIONS = {
    "guest": ["send_message", "view_users"],
    "moderator": ["send_message", "view_users", "view_logs"],
    "admin": ["send_message", "view_users", "view_logs", "shutdown_server"]
}

def has_permission(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, [])