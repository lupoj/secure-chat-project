import socket
import threading
import json
import getpass
import ssl

# Define a function to send JSON packets over a socket connection
def send_json_packets(client, data):

    # Convert the data to a JSON string and send it over the socket connection, handling any exceptions that may occur during sending
    try:

        client.send(json.dumps(data).encode())

    except Exception as e:

        print("Error sending data:", e)

# Define a function to receive JSON packets from a socket connection
def receive_json_packets(client):

    # Attempt to receive data from the socket connection, decode it, and parse it as JSON, handling any exceptions that may occur during receiving or parsing
    try:

        data = client.recv(8192).decode()
        return json.loads(data) if data else None
    
    except Exception:

        return None

# Define a function to handle the authentication handshake between the client and server
def auth_handshake(client):

    # Enter a loop to continuously receive packets from the server and handle authentication-related actions based on the received packet's status
    while True:

        # Receive a packet from the server and check if it is valid, handling the case where the server closes the connection during authentication
        packet = receive_json_packets(client)
        if not packet:

            print("Server closed connection during authentication.")
            return False

        # Extract the status from the received packet and handle different authentication-related actions based on the status value
        status = packet.get("status")

        # Handle the case where the server requests authentication from the client, prompting the user to select an option for login or registration and sending the corresponding request to the server
        if status == "AUTH_MENU":

            print("Please select an option:")
            print("1. Login")
            print("2. Register New Account")

            # Enter a loop to prompt the user for a valid choice (1 or 2) and handle invalid input by displaying an error message
            while True:

                choice = input("Select (1/2): ").strip()

                if choice in ["1", "2"]:
                    break

                else:

                    print("Invalid choice. Please enter 1 or 2.")

            # Determine the action based on the user's choice (login or register) and prompt the user for their username and password, sending the authentication request payload to the server
            action = "login" if choice == "1" else "register"
            username = input("Username: ").strip()
            password = getpass.getpass("Password: ").strip()

            # Send authentication request payload
            send_json_packets(client, {"action": action, "username": username, "password": password})

        elif status == "AUTH_SUCCESS":      # Handle the case where the server indicates successful authentication

            # Extract the username and role from the received packet and display a success message indicating that the user has logged in successfully, returning True to indicate successful authentication
            user = packet.get("username")
            role = packet.get("role", "guest")
            print(f"\nLogin Successful: Logged in as '{user}' [{role.upper()}]")
            return True

        elif status == "AUTH_FAIL":     # Handle the case where the server indicates failed authentication, displaying an error message with the reason for failure

            print(f"\nLogin Failed: {packet.get('message')}")

        elif status == "REG_SUCCESS":   # Handle the case where the server indicates successful registration of a new user, displaying a success message with the server's response

            print(f"\nRegistration Successful: {packet.get('message')}")

        elif status == "REG_FAIL":   # Handle the case where the server indicates failed registration of a new user, displaying an error message with the reason for failure

            print(f"\nRegistration Failed: {packet.get('message')}")

# Define a function to initialize the client, establish a secure TLS connection to the server, and handle user input for sending messages or performing actions
def initialize_client():
    # Define the server host and port for the client to connect to
    host = "127.0.0.1"
    port = 12346

    # Create an SSL context for the client, disabling hostname checking and certificate verification for testing purposes
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Create a TCP socket for the client to connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Attempt to wrap the socket with the SSL context and connect to the server, handling any exceptions that may occur during the connection process
    try:
        # Wrap the socket with the SSL context to establish a secure TLS connection to the server, specifying the server hostname for SNI (Server Name Indication)
        secure_client = ssl_context.wrap_socket(client, server_hostname = host)
        secure_client.connect((host, port))
        print("\nSecurely connected to the server via TLS at", host, "on port", port)

        # Set socket options for the secure client, including disabling timeouts and enabling keep-alive to maintain the connection
        secure_client.settimeout(None)
        secure_client.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    except Exception as e:  # Handle any exceptions that may occur during the TLS connection process, printing an error message and returning from the function

        print(f"Error connecting via TLS: {e}")
        return

    # Enter a loop to continuously handle authentication and user input for sending messages or performing actions, allowing the user to log out and switch accounts if desired
    while True:

        # Perform the authentication handshake with the server, and if authentication fails, break out of the loop to terminate the client
        auth_success = auth_handshake(secure_client)
        if not auth_success:
            break

        # Create a threading event to signal when the message receiving thread should stop, and start a new thread to handle receiving messages from the server
        stop_listener = threading.Event()

        # Start a new thread to handle receiving messages from the server, passing the secure client socket and the stop_listener event as arguments to the receive_messages function
        client_thread = threading.Thread(target=receive_messages, args=(secure_client, stop_listener))
        client_thread.daemon = True
        client_thread.start()

        # Prompt the user to enter messages or commands, allowing them to send messages, view users, view logs, 
        # or shut down the server based on their role and permissions, and handle user input in a loop until they choose to log out or exit the client
        print("Type your message below (type '/logout' to switch accounts, or 'exit' to quit): ")
        user_logged_out = False
        while True:

            # Prompt the user to enter a message or command, and handle their input accordingly, sending the appropriate JSON packets to the server based on their actions
            try:

                # Prompt the user to enter a message or command, and strip any leading or trailing whitespace from their input
                message = input("Enter message: ").strip()

                # Check if the user entered "exit" to quit the client, and if so, set the stop_listener event, close the secure client socket, 
                # and print a disconnection message before returning from the function
                if message.lower() == "exit":
                
                    stop_listener.set()
                    secure_client.close()
                    print("Disconnected from server.")
                    return

                # Handle user commands for logging out, viewing users, viewing logs, or shutting down the server based on their input, sending the appropriate JSON packets to the server
                if message:

                    # Check if the user entered "/logout" to log out and switch accounts, and if so, send a logout request to the server, set the stop_listener event,
                    if message == "/logout":

                        send_json_packets(secure_client, {"action": "logout"})      # Send a logout request to the server

                        stop_listener.set()
                        user_logged_out = True
                        print("\nLogging out.")
                        break

                    elif message == "/users":   # Handle the case where the user entered "/users" to view the list of users, sending a request to the server to retrieve the user list

                        send_json_packets(secure_client, {"action": "view_users"})

                    elif message == "/logs":    # Handle the case where the user entered "/logs" to view the server logs, sending a request to the server to retrieve the logs

                        send_json_packets(secure_client, {"action": "view_logs"})

                    elif message == "/shutdown":    # Handle the case where the user entered "/shutdown" to shut down the server, checking if they have permission to perform this action and sending a request to the server if they do

                        send_json_packets(secure_client, {"action" : "shutdown_server"})
                    
                    else:   # Handle the case where the user entered a regular message to send to the server, sending the message in a JSON packet to the server for processing

                        send_json_packets(secure_client, {"action": "send_message", "message": message})
                        
            except Exception as e:  # Handle any exceptions that may occur during user input or message sending, printing an error message and breaking out of the loop to terminate the client

                print("Error occurred while sending message.", e)
                break

        client_thread.join(timeout=1.0) # Wait for the message receiving thread to finish, with a timeout of 1 second to prevent blocking indefinitely

        # If the user did not log out, break out of the outer loop to terminate the client, otherwise continue to allow them to log in with a different account
        if not user_logged_out:
            break

    # Close the secure client socket and print a disconnection message before returning from the function
    secure_client.close()
    print("Disconnected from the server.")

# Define a function to receive messages from the server in a separate thread, continuously listening for incoming packets and handling them based on their status and content
def receive_messages(client, stop_listener):

    # Enter a loop to continuously receive packets from the server and handle them based on their status and content, until the stop_listener event is set or an error occurs
    while not stop_listener.is_set(): 

        # Attempt to receive a packet from the server and handle it based on its status and content, breaking out of the loop if an error occurs or the server closes the connection
        try:

            packet = receive_json_packets(client)

            # Check if the received packet is None, indicating that the server has closed the connection, and if so, print a disconnection message and break out of the loop
            if packet is None: 

                if not stop_listener.is_set():

                    print("\nDisconnected from the server.")

                break

            # Extract the status and message from the received packet, and handle different statuses such as logout success, 
            # chat messages, errors, or informational messages, printing them to the console
            status = packet.get("status")
            message = packet.get("message", "")

            # Handle the case where the server indicates successful logout, printing a message and breaking out of the loop to terminate the message receiving thread
            if status == "LOGOUT_SUCCESS":

                print(f"\n {message}")
                break

            # Handle the case where the server sends a chat message, printing it to the console, or handle error and informational messages by printing them with appropriate formatting
            if status == "CHAT_MSG":

                print(f"\n{message}")

            elif status in ["ERROR", "INFO"]:   # Handle error and informational messages from the server, printing them with appropriate formatting based on their status

                print(f"\n[{status}] {message}")

            else:   # Handle any other statuses from the server by printing the message to the console without additional formatting

                print(f"\n{message}")

            # If the stop_listener event is not set, prompt the user to enter a message, ensuring that the prompt appears on the same line as the user's input for an organized user interface
            if not stop_listener.is_set(): 

                print("Enter message: ", end="", flush=True)

        except Exception:   # Handle any exceptions that may occur during message receiving or processing, breaking out of the loop to terminate the message receiving thread and allowing the client to handle the disconnection gracefully
            break

# Call the initialize_client function to start the client application when the script is run directly
if __name__ == "__main__":
    initialize_client()