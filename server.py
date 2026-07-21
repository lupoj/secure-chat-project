import socket
import threading

clients = []

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
        clients.append(connection)

        new_thread = threading.Thread(target=current_client, args=(connection, address))
        new_thread.start()

def current_client(conn, address):
    print("Handling client", address)

    conn.settimeout(None)

    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    while True:
        try:
            message = conn.recv(1024).decode()

            if not message:
                print("Client", address, "disconnected from the server.")
                break

            print("Received message from", address, ":", message)

            broadcast(message, conn)    

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
                client.send(message.encode())
            except Exception as e:
                print("Error occurred while broadcasting to a client.")
                clients.remove(client)
                client.close()

if __name__ == "__main__":
    initialize_server()