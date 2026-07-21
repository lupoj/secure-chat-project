import socket
import threading

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
    
    username = input("Enter your username: ")

    client_thread = threading.Thread(target=receive_messages, args=(client,))
    client_thread.daemon = True
    client_thread.start()

    initial_message = username + " has joined the chat."
    client.send(initial_message.encode())
    
    while True:

        try:
            message = input("Enter message: ")
            if message.lower() == "exit":
                break

            if message.strip():
                final_message = username + ": " + message + "\n"
                client.send(final_message.encode())
        except Exception as e:
            print("Error occurred while sending message.")
            break

    client.close()
    print("Disconnected from the server.")

def receive_messages(client):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                print("Disconnected from the server.")
                break

            print(message.decode().strip())
        except:
            print("Error occurred while receiving message.")
            break
    
    client.close()

if __name__ == "__main__":
    initialize_client()