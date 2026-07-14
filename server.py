import socket
import threading

clients = []

def initialize_server():
    host = "127.0.0.1"
    port = 12345

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    print("Server is listening for connections on port", port)

    while True:
        connection, address = server.accept()
        print("New connection from", address)
        clients.append(connection)

        new_thread = threading.Thread(target=current_client, args=(connection, address))
        new_thread.start()

def current_client(connection, address):
    print("Handling client", address)

    connection.send("Welcome to the server!".encode())

    while True:
        try:
            message = connection.recv(1024)

            if not message:
                print("Client", address, "disconnected from the server.")
                break

            decoded_data = message.decode()
            print("Received message from", address, ":", decoded_data.strip())

            # Broadcast the message to all other clients
            for i in clients:
                if i != connection:
                    try:
                        i.send(message)
                    except:
                        if i in clients:
                            clients.remove(i)
        
        except:
            print("Error occurred with client", address)
            break

        if connection in clients:
            clients.remove(connection)
        connection.close()
        print("Connection with client", address, "closed.")

if __name__ == "__main__":
    initialize_server()