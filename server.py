import socket
import threading
import json
from auth import authenticate_user, register_user
from security import has_permission

clients = []

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
        # clients.append(connection)

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
        data = conn.recv(1024).decode()
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
    
    clients.append(conn)

    new_user_message = f"SERVER: {username} [{role.upper()}] has joined the chat."
    broadcast(new_user_message, conn)

    while True:
        try:
            json_packet = receive_json_packets(conn)

            if not json_packet:
                print("Client", address, "disconnected from the server.")
                break

            action = json_packet.get("action", "send_message")
            client_message = json_packet.get("message", "")

            if not has_permission(role, action):
                send_json_packets(conn, {"status": "ERROR", "message": f"Permission Denied: Role [{role.upper()}] cannot perform '{action}'."})
                continue

            print(f"[{role.upper()}] {username}: {client_message}")

            complete_msg = f"[{role.upper()}] {username}: {client_message}"
            broadcast(complete_msg, conn)

        except Exception as e:
            print("Error occurred with client", address)
            break

    if conn in clients:
        clients.remove(conn)
    conn.close()
    print("Connection with client", address, "closed.")

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                json_packet = {"status": "CHAT_MSG", "message": message}
                client.send(json.dumps(json_packet).encode())
            except Exception as e:
                print("Error occurred while broadcasting to a client.")
                if client in clients:
                    clients.remove(client)
                client.close()

if __name__ == "__main__":
    initialize_server()