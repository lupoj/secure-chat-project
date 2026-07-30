import socket
import threading
import json
import getpass
import ssl

def send_json_packets(client, data):
    try:
        client.send(json.dumps(data).encode())
    except Exception as e:
        print("Error sending data:", e)

def receive_json_packets(client):
    try:
        data = client.recv(8192).decode()
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

            while True:
                choice = input("Select (1/2): ").strip()

                if choice in ["1", "2"]:
                    break
                else:
                    print("Invalid choice. Please enter 1 or 2.")

            action = "login" if choice == "1" else "register"
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ").strip()

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
    port = 12346

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        secure_client = ssl_context.wrap_socket(client, server_hostname = host)
        secure_client.connect((host, port))
        print("\nSecurely connected to the server via TLS at", host, "on port", port)
        print(f"Active Cipher Suite: {secure_client.cipher()}")

        secure_client.settimeout(None)
        secure_client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    except Exception as e:
        print(f"Error connecting via TLS: {e}")
        return

    while True:
        auth_success = auth_handshake(secure_client)
        if not auth_success:
            break
            #secure_client.close()
            #return

        #logout_requested = [False]
        stop_listener = threading.Event()

        client_thread = threading.Thread(target=receive_messages, args=(secure_client, stop_listener))
        client_thread.daemon = True
        client_thread.start()

        print("Type your message below (type '/logout' to switch accounts, or 'exit' to quit): ")
        user_logged_out = False

        while True:

            try:
                message = input("Enter message: ").strip()

                if message.lower() == "exit":
                    #break
                    stop_listener.set()
                    secure_client.close()
                    print("Disconnected from server.")
                    return

                if message:

                    if message == "/logout":
                        send_json_packets(secure_client, {"action": "logout"})
                        #logout_requested[0] = True

                        stop_listener.set()
                        user_logged_out = True
                        print("\nLogging out.")
                        break

                    elif message == "/users":
                        send_json_packets(secure_client, {"action": "view_users"})

                    elif message == "/logs":
                        send_json_packets(secure_client, {"action": "view_logs"})

                    elif message == "/shutdown":
                        send_json_packets(secure_client, {"action" : "shutdown_server"})
                    
                    else:
                        send_json_packets(secure_client, {
                            "action": "send_message",
                            "message": message
                        })
                        
            except Exception as e:
                print("Error occurred while sending message.", e)
                #logout_requested[0] = True
                break

        client_thread.join(timeout=1.0)

        if not user_logged_out:
            break

    secure_client.close()
    print("Disconnected from the server.")

def receive_messages(client, stop_listener):
    while not stop_listener.is_set(): #logout_requested[0]
        try:
            packet = receive_json_packets(client)
            if packet is None: # Used to be if not packet
                if not stop_listener.is_set():
                    print("\nDisconnected from the server.")
                break

            status = packet.get("status")
            message = packet.get("message", "")

            if status == "LOGOUT_SUCCESS":
                print(f"\n {message}")
                break

            if status == "CHAT_MSG":
                print(f"\n{message}")
            elif status in ["ERROR", "INFO"]:
                print(f"\n[{status}] {message}")
            else:
                print(f"\n{message}")

            if not stop_listener.is_set(): #logout_requested[0]
                print("Enter message: ", end="", flush=True)

        except Exception:
            #if not logout_requested[0]:
                #print("\nError occurred while receiving message.")
            break
    
    #client.close()

if __name__ == "__main__":
    initialize_client()