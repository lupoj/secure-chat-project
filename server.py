import socket
import threading
import json
import datetime
import os
import ssl
from auth import authenticate_user, register_user
from security import has_permission

# Dictionary to keep track of active clients
active_clients = {}

# Logging function to write audit logs to a file
def logs(username, role, action, message=""):
    time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")    # Format the timestamp as YYYY/MM/DD HH:MM:SS

    log_entry = f"[{time}] USER: {username} - ROLE: {role} - ACTION: {action} - MESSAGE: {message}\n"   # Template for log entry creation

    # Append the log entry to the audit.log file
    with open("audit.log", "a") as f:
        f.write(log_entry)

# Initialize the server and listen for incoming connections
def initialize_server():
    host = "127.0.0.1"
    port = 12346

    # Create an SSL context for secure connections
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")    # Load the server's certificate and private key for TLS encryption

    # Create a TCP socket and bind it to the specified host and port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    print("Server is listening for connections on port", port)

    # Accept incoming connections and handle them in dedicated threads
    while True:
        connection, address = server.accept()   # Accept a new client connection

        # Wrap the connection with SSL for secure connections and handle any SSL handshake errors
        try:
            secure_connection = ssl_context.wrap_socket(connection, server_side = True)
            print("New Secure TLS connection from", address)

            new_thread = threading.Thread(target=current_client, args=(secure_connection, address))
            new_thread.start()

        except ssl.SSLError as e:
            print(f"SSL Handshake failed for {address}: {e}")
            connection.close()

# Handle sending and receiving JSON packets
def send_json_packets(conn, data):

    # Convert the data to JSON format and send it over the connection
    try:
        conn.send(json.dumps(data).encode())

    except Exception as e:                                      # Handle any exceptions that occur during the sending of JSON packets
        print("Error occurred while sending JSON packet:", e)

# Handle receiving JSON packets from a client connection
def receive_json_packets(conn):
    # Receive data from the connection and decode it from JSON format
    try:
        data = conn.recv(8192).decode()
        return json.loads(data) if data else None
    
    except Exception:       # Handle any exceptions that occur during the receiving of JSON packets
        return None

# Handle the authentication process for a client connection
def handle_auth(conn, address):

    # Loop to continuously prompt the client for authentication actions (login or register)
    while True:

        send_json_packets(conn, {"status": "AUTH_MENU", "message": "1, Login\n2. Register"})    # Send a JSON packet to the client with the authentication menu options
        request = receive_json_packets(conn)    # Receive a JSON packet from the client containing the authentication request

        # Check if the request is None, indicating that the client has disconnected during authentication
        if not request:
            conn.close()
            print("Client", address, "disconnected during authentication.")
            return None, None

        # Get the action, username, and password from the received request
        action = request.get("action")
        username = request.get("username", "").strip()
        password = request.get("password", "").strip()

        # Handle the login action by authenticating the user with the provided username and password
        if action == "login":

            success, role, message = authenticate_user(username, password)      # Call the authenticate_user function to verify the provided credentials and retrieve the user's role and any given message

            # If authentication is successful, send a success response to the client and log the successful login attempt
            if success:

                send_json_packets(conn, {"status": "AUTH_SUCCESS", "username": username, "role": role})
                print("Client", address, "authenticated as", username, "with role", role)
                return username, role
            
            else:   # If authentication fails, send a failure response to the client and log the failed login attempt

                send_json_packets(conn, {"status": "AUTH_FAIL", "message": message})
                safe_username = username if username else "UNKNOWN"

                logs(safe_username, "unauthenticated", "login_failed", f"Failed login attempt from {address} - Reason: {message}")

        elif action == "register":  # Handle the register action by registering a new user with the provided username and password

            success, message = register_user(username, password)

            # If registration is successful, send a success response to the client and log the successful registration attempt
            if success:

                send_json_packets(conn, {"status": "REG_SUCCESS", "message": message})
                print("Client", address, "registered as", username)
                logs(username, "guest", "register_success", f"New user registered from {address}")

            else:   # If registration fails, send a failure response to the client and log the failed registration attempt

                send_json_packets(conn, {"status": "REG_FAIL", "message": message})

                safe_username = username if username else "UNKNOWN"
                logs(safe_username, "unauthenticated", "register_failed", f"Registration failed ({message}) from {address}")

# Handle the current client connection, including authentication, message handling, and broadcasting messages to other clients
def current_client(conn, address):
    print("Handling client", address)

    # Set socket options for the client connection to ensure proper behavior and keep-alive functionality
    conn.settimeout(None)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    # Loop to continuously handle the client's actions after successful authentication
    while True:

        username, role = handle_auth(conn, address)     # Call the handle_auth function to authenticate the client and retrieve the username and role

        # If authentication fails (username is None), close the connection and log the failure
        if not username:
            conn.close()
            print("Connection with client", address, "closed due to authentication failure.")
            return

        # Add the authenticated client to the active_clients dictionary for tracking
        active_clients[username] = conn

        # Log the successful login and broadcast a message to other clients indicating that a new user has joined the chat
        logs(username, role, "login", f"User logged in from {address}")
        new_user_message = f"SERVER: {username} [{role.upper()}] has joined the chat."
        broadcast(new_user_message, conn, sender_username="SERVER")

        # Set a flag to track whether the client has logged out, and enter a loop to handle the client's actions
        logout_flag = False
        while True:

            # Receive a JSON packet from the client and handle the requested action, including sending messages, viewing users, viewing logs, logging out, and shutting down the server
            try:

                json_packet = receive_json_packets(conn)

                # Check if the received JSON packet is None, indicating that the client has disconnected
                if not json_packet:
                    print("Client", address, f"({username}) disconnected from the server.")
                    break

                # Get the action and message from the received JSON packet, defaulting to "send_message" if no action is specified
                action = json_packet.get("action", "send_message")
                client_message = json_packet.get("message", "")

                # Log the action performed by the client, including the username, role, action, and any message provided
                logs(username, role, action, client_message)

                # Handle the logout action by logging the logout event, broadcasting a message to other clients, sending a success response to the client, and setting the logout flag to True
                if action == "logout":

                    # Log the logout event and print a message indicating that the client has logged out
                    logs(username, role, "logout", f"User logged out from {address}.")
                    print(f"Client {address} ({username}) logged out.")

                    # Broadcast a message to other clients indicating that the user has logged out
                    broadcast(f"SERVER: {username} has logged out.", conn, sender_username="SERVER")

                    # Send a success response to the client indicating that the logout was successful
                    send_json_packets(conn, {"status": "LOGOUT_SUCCESS", "message": "Logged out successfully."})
                    logout_flag = True  # Set the logout flag to True to indicate that the client has logged out
                    break

                elif not has_permission(role, action):  # Check if the client has permission to perform the requested action based on their role, and handle permission denial by logging the event and sending an error response to the client

                    # Log the permission denial event and send an error response to the client indicating that the action is not allowed for their role
                    logs(username, role, action, f"User {address} attempted to perform ({action}) and was denied")
                    send_json_packets(conn, {"status": "ERROR", "message": f"Permission Denied: Role [{role.upper()}] cannot perform '{action}'."})
                    continue

                elif action == "view_users":    # Handle the view_users action by logging the event and sending a response to the client with the count of connected users

                    logs(username, role, "view_users", f"Users viewed from {address}")
                    send_json_packets(conn, {"status": "INFO", "message": f"Connected users count: {len(active_clients)}"})

                elif action == "view_logs": # Handle the view_logs action by attempting to read the audit.log file and sending the recent logs to the client, while handling any exceptions that may occur during file access

                    # Attempt to read the audit.log file and send the recent logs to the client, while handling any exceptions that may occur during file access
                    try:

                        # Check if the audit.log file exists before attempting to read it, and handle the case where the file is not found by logging the event and sending an informational response to the client
                        if not os.path.exists("audit.log"):

                            logs(username, role, "view_logs", f"User from {address} failed to open log file: File not found")
                            send_json_packets(conn, {"status": "INFO", "message": "No log file found."})

                        else:   # If the audit.log file exists, read the last 10 lines of the file and send them to the client, while logging the successful access of the log file

                            # Read the last 10 lines of the audit.log file and send them to the client, while logging the successful access of the log file
                            with open("audit.log", "r") as file:

                                lines = file.readlines()
                                recent_logs = "".join(lines[-10:]) if lines else "No logs available."

                                logs(username, role, "view_logs", f"User from {address} successfully opened log file")
                                send_json_packets(conn, {"status": "INFO", "message": f"\n-----AUDIT LOGS-----\n{recent_logs}"})

                    except Exception as read_err:   # Handle any exceptions that occur while reading the audit.log file by logging the error and sending an error response to the client

                        print(f"Error reading audit.log for {username}: {read_err}")
                        send_json_packets(conn, {"status": "ERROR", "message": "No log file found."})
                
                    continue    # Continue to the next iteration of the loop to wait for the next action from the client

                elif action == "shutdown_server":   # Handle the shutdown_server action by logging the event, broadcasting a shutdown message to other clients, closing all active client connections, and terminating the server process

                    logs(username, role, "shutdown", f"Server shutdown initiated by user from {address}.")
                    print(f"[ADMIN ACTION] Server shutdown initiated by {username}.")
                    broadcast("SERVER: The server is shutting down now.", conn, sender_username="SERVER")

                    logs("SERVER", "system", "server_shutdown", "Server process terminated.")

                    # Close all active client connections and clear the active_clients dictionary before terminating the server process
                    for active_user, client in list(active_clients.items()):

                        # Attempt to close each active client connection and handle any exceptions that may occur during the closing process
                        try:

                            client.close()

                        except Exception:

                            pass

                    # Clear the active_clients dictionary to remove all entries and terminate the server process using os._exit(0)
                    active_clients.clear()
                    os._exit(0)


                elif action == "send_message":  # Handle the send_message action by logging the event, printing the message to the server console, and broadcasting the message to other clients

                    complete_msg = f"[{role.upper()}] {username}: {client_message}"
                    logs(username, role, "send_message", f"({complete_msg}) sent from {address}")
                    print(complete_msg)
                    broadcast(complete_msg, conn, sender_username=username)

            except Exception as e:  # Handle any exceptions that occur during the processing of client actions by logging the error and breaking the loop to close the connection

                print("Error occurred with client", address)
                break

        # Remove the client from the active_clients dictionary and close the connection if the client has logged out or disconnected
        if username in active_clients: 

            del active_clients[username]

        # Close the connection and print a message indicating that the connection with the client has been closed if the logout flag is not set
        if not logout_flag:

            conn.close()
            print("Connection with client", address, "has been closed.")
            return

# Broadcast a message to all connected clients except the sender, indicating that a new message has been sent
def broadcast(message, sender_socket, sender_username="SERVER"):

    json_packet = {"status": "CHAT_MSG", "message": message}    # Create a JSON packet containing the status and message to be broadcasted to all connected clients

    # Loop through all active clients and send the JSON packet to each client except the sender, while handling any exceptions that may occur during the sending process
    for curr_username in list(active_clients.keys()):

        client_socket = active_clients.get(curr_username)   # Get the client socket for the current username from the active_clients dictionary

        # Check if the client socket is None or if it is the same as the sender's socket, and skip sending the message to that client if either condition is true
        if not client_socket or client_socket == sender_socket:
            
            continue

        # Attempt to send the JSON packet to the client socket and handle any exceptions that may occur during the sending process, 
        # including logging the error and removing the client from the active_clients dictionary if necessary
        try:

            client_socket.send(json.dumps(json_packet).encode())    # Send the JSON packet to the client socket after encoding it to bytes using JSON serialization

        except Exception as e:  

            print(f"Error occurred while broadcasting to a client: {e}")

            # Remove the client from the active_clients dictionary if the client socket is no longer valid or if an error occurred during sending
            if curr_username in active_clients:

                del active_clients[curr_username]

            # Close the client socket to free up resources and continue to the next client in the loop    
            client_socket.close()
            continue

        # Attempt to log the message broadcast event for the current username, and handle any exceptions that may occur during logging
        try:

            logs(str(curr_username), "user", "receive_message", message)

        except Exception as log_err:

            print(f"Logging error for {curr_username}: {log_err}")

# Entry point of the server script, which initializes the server and starts listening for incoming connections
if __name__ == "__main__":
    initialize_server()