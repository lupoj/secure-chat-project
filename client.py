import socket
import threading
import json

def send_json_packets(client, data):
    try:
        client.send(json.dumps(data).encode())
    except Exception as e:
        print("Error sending data:", e)

def receive_json_packets(client):
    try:
        data = client.recv(1024).decode()
        return json.loads(data) if data else None
    except Exception:
        return None
    
def auth_handshake(client):

    while True:
        packet = receive_json_packets(client)
        if not packet:
            print("Server closed connection during authentication.")
            return False

        status = packet.get("status")

        if status == "AUTH_MENU":
            print("\n" + "="*35)
            print("Welcome! Please select an option:")
            print("1. Login")
            print("2. Register New Account")
            choice = input("Select (1/2): ").strip()

            if choice not in ["1", "2"]:
                print("Invalid choice. Please enter 1 or 2.")
                continue

            action = "login" if choice == "1" else "register"
            username = input("Username: ").strip()
            password = input("Password: ").strip()

            # Send authentication request payload
            send_json_packets(client, {
                "action": action,
                "username": username,
                "password": password
            })

        elif status == "AUTH_SUCCESS":
            user = packet.get("username")
            role = packet.get("role", "guest")
            print(f"\n✅ Success! Logged in as '{user}' [{role.upper()}]")
            print("="*35 + "\n")
            return True

        elif status == "AUTH_FAIL":
            print(f"\n❌ Login Failed: {packet.get('message')}")

        elif status == "REG_SUCCESS":
            print(f"\n✅ Registration Successful! {packet.get('message')}")

        elif status == "REG_FAIL":
            print(f"\n❌ Registration Failed: {packet.get('message')}")


def initialize_client():
    host = "127.0.0.1"
    port = 54321

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((host, port))
        print("Connected to the server at", host, "on port", port)

        client.settimeout(None)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    except Exception as connect_error:
        print("Error:", connect_error)
        return
    
    auth_success = auth_handshake(client)
    if not auth_success:
        client.close()
        return

    client_thread = threading.Thread(target=receive_messages, args=(client,))
    client_thread.daemon = True
    client_thread.start()

    print("Type your message below (type 'exit' to quit): ")

    while True:

        try:
            message = input("Enter message: ").strip()
            if message.lower() == "exit":
                break

            if message:
                send_json_packets(client, {
                    "action": "send_message",
                    "message": message
                })
        except Exception as e:
            print("Error occurred while sending message.")
            break

    client.close()
    print("Disconnected from the server.")

def receive_messages(client):
    while True:
        try:
            packet = receive_json_packets(client)
            if not packet:
                print("Disconnected from the server.")
                break

            status = packet.get("status")
            message = packet.get("message", "")

            if status == "CHAT_MSG":
                print(f"\n{message}")
            elif status in ["ERROR", "INFO"]:
                print(f"\n[{status}] {message}")
            else:
                print(f"\n{message}")

            print("Enter message: ", end="", flush=True)

        except:
            print("Error occurred while receiving message.")
            break
    
    client.close()

if __name__ == "__main__":
    initialize_client()