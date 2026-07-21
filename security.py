PERMISSIONS = {
    "guest": ["send_message", "view_users"],
    "moderator": ["send_message", "view_users", "kick_user", "mute_user"],
    "admin": ["send_message", "view_users", "kick_user", "mute_user", "view_logs", "shutdown_server"]
}

def has_permission(role: str, action: str) -> bool:
    return action in PERMISSIONS.get(role, [])