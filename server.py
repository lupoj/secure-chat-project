import socket
import threading
import json
import datetime
import os
from auth import authenticate_user, register_user
from security import has_permission

active_clients = {}

def logs(username, role, action, message=""):
    time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    log_entry = f"[{time}] USER: {username} - ROLE: {role} - ACTION: {action} - MESSAGE: {message}\n"

    with open("audit.log", "a") as f:
        f.write(log_entry)

# Initialize the server and listen for incoming connections
def initialize_server():
    host = "127.0.0.1"
    port = 54321

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print("Server is listening for connections on port", port)

    while True:
        connection, address = server.accept()
        print("New connection from", address)

        new_thread = threading.Thread(target=current_client, args=(connection, address))
        new_thread.start()

# Handle sending and receiving JSON packets
def send_json_packets(conn, data):
    try:
        conn.send(json.dumps(data).encode())
    except Exception as e:
        print("Error occurred while sending JSON packet:", e)

def receive_json_packets(conn):
    try:
        data = conn.recv(8192).decode()
        return json.loads(data) if data else None
    except Exception:
        return None
    
def handle_auth(conn, address):

    while True:
        send_json_packets(conn, {"status": "AUTH_MENU", "message": "1, Login\n2. Register"})
        request = receive_json_packets(conn)

        if not request:
            print("Client", address, "disconnected during authentication.")
            return None, None
        
        action = request.get("action")
        username = request.get("username", "").strip()
        password = request.get("password", "").strip()

        if action == "login":
            success, role = authenticate_user(username, password)

            if success:
                send_json_packets(conn, {"status": "AUTH_SUCCESS", "username": username, "role": role})
                print("Client", address, "authenticated as", username, "with role", role)
                return username, role
            else:
                send_json_packets(conn, {"status": "AUTH_FAIL", "message": "Invalid username or password."})

        elif action == "register":
            success, message = register_user(username, password)

            if success:
                send_json_packets(conn, {"status": "REG_SUCCESS", "message": message})
                print("Client", address, "registered as", username)
            else:
                send_json_packets(conn, {"status": "REG_FAIL", "message": message})

def current_client(conn, address):
    print("Handling client", address)

    conn.settimeout(None)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    username, role = handle_auth(conn, address)

    if not username:
        conn.close()
        print("Connection with client", address, "closed due to authentication failure.")
        return
    
    active_clients[username] = conn

    logs(username, role, "login", "User logged in")
    new_user_message = f"SERVER: {username} [{role.upper()}] has joined the chat."
    broadcast(new_user_message, conn, sender_username="SERVER")

    while True:
        try:
            json_packet = receive_json_packets(conn)

            if not json_packet:
                print("Client", address, "disconnected from the server.")
                break

            action = json_packet.get("action", "send_message")
            client_message = json_packet.get("message", "")

            logs(username, role, action, client_message)

            if not has_permission(role, action):
                send_json_packets(conn, {"status": "ERROR", "message": f"Permission Denied: Role [{role.upper()}] cannot perform '{action}'."})
                continue

            elif action == "view_users":
                
                users = ", ".join(active_clients.keys())
                send_json_packets(conn, {
                    "status": "INFO",
                    "message": f"Connected users count: {len(active_clients)}"
                })

            elif action == "view_logs":

                try:
                    if not os.path.exists("audit.log"):
                        send_json_packets(conn, {"status": "INFO", "message": "No log file found."})

                    else:

                        file = open("audit.log", "r")
                        try:
                            lines = file.readlines()
                            recent_logs = "".join(lines[-10:]) if lines else "No logs available."
                            send_json_packets(conn, {
                                "status": "INFO",
                                "message": f"\n-----AUDIT LOGS-----\n{recent_logs}"
                            })
                        finally:
                            file.close()

                except Exception as read_err:
                    print(f"Error reading audit.log for {username}: {read_err}")
                    send_json_packets(conn, {"status": "ERROR", "message": "No log file found."})
            
                continue

            elif action == "shutdown_server":
                logs(username, role, "shutdown", "Server shutdown initiated by user.")
                print(f"[ADMIN ACTION] Server shutdown initiated by {username}.")
                broadcast("SERVER: The server is shutting down now.", conn, sender_username="SERVER")

                logs("SERVER", "system", "server_shutdown", "Server process terminated.")

                for active_user, client in list(active_clients.items()):
                    try:
                        client.close()
                    except Exception:
                        pass

                active_clients.clear()


            elif action == "send_message":
                complete_msg = f"[{role.upper()}] {username}: {client_message}"
                print(complete_msg)
                broadcast(complete_msg, conn, sender_username=username)

        except Exception as e:
            print("Error occurred with client", address)
            break

    if username in active_clients:
        del active_clients[username]
    conn.close()

    print("Connection with client", address, "closed.")

def broadcast(message, sender_socket, sender_username="SERVER"):
    json_packet = {"status": "CHAT_MSG", "message": message}

    for curr_username in list(active_clients.keys()):
        client_socket = active_clients.get(curr_username)

        if not client_socket or client_socket == sender_socket:
            continue

        try:
            client_socket.send(json.dumps(json_packet).encode())

        except Exception as e:
            print(f"Error occurred while broadcasting to a client: {e}")

            if curr_username in active_clients:
                del active_clients[curr_username]
            client_socket.close()
            continue

        try:
            logs(str(curr_username), "user", "receive_message", message)
        except Exception as log_err:
            print(f"Logging error for {curr_username}: {log_err}")

if __name__ == "__main__":
    initialize_server()